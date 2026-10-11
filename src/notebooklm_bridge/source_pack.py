"""Create safe, portable source bundles for personal NotebookLM.

The consumer NotebookLM website does not expose a supported public API for
creating personal notebooks and uploading arbitrary sources. This bridge
therefore packages teacher-selected originals and descriptive indexes for
manual import, while preserving the existing document catalog and storage.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Callable, Iterable

from teacher_document_library_v2.models import TeacherDocument

DEFAULT_MAX_TOTAL_BYTES = 100 * 1024 * 1024
MAX_SOURCE_FILENAME_LENGTH = 180
DownloadDocument = Callable[[TeacherDocument], bytes]


class NotebookLMSourcePackError(ValueError):
    """Raised when a source pack cannot be produced safely."""


@dataclass(frozen=True)
class NotebookLMSourcePack:
    filename: str
    content: bytes
    included_sources: tuple[dict[str, object], ...]
    failed_sources: tuple[dict[str, str], ...]


def _safe_filename(value: str) -> str:
    """Return a single safe archive filename, never a path supplied by a source."""
    raw = str(value or "source.bin").replace("\\", "/").split("/")[-1].strip()
    raw = re.sub(r"[\x00-\x1f<>:\"/|?*]", "_", raw)
    raw = raw.strip(" .")
    if not raw or raw in {".", ".."}:
        raw = "source.bin"
    if len(raw) > MAX_SOURCE_FILENAME_LENGTH:
        dot = raw.rfind(".")
        suffix = raw[dot:] if 0 < dot < len(raw) - 1 else ""
        stem = raw[:dot] if suffix else raw
        raw = stem[: MAX_SOURCE_FILENAME_LENGTH - len(suffix)] + suffix
    return raw


def _markdown_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def _metadata(document: TeacherDocument, index: int, archive_path: str, content: bytes) -> dict[str, object]:
    return {
        "sequence": index,
        "document_id": document.document_id,
        "title": document.title,
        "category": document.category.value,
        "category_label": document.category_label,
        "academic_year": document.academic_year,
        "subject": document.subject,
        "grade_level": document.grade_level,
        "class_name": document.class_name,
        "file_name": document.file_name,
        "archive_path": archive_path,
        "mime_type": document.mime_type,
        "size_bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "storage_provider": document.storage_provider,
        "web_view_link": document.web_view_link,
        "description": document.description,
        "tags": list(document.tags),
    }


def _readme(created_at: str, included: list[dict[str, object]], failed: list[dict[str, str]]) -> str:
    lines = [
        "# Gói nguồn MathTeacher AI → NotebookLM",
        "",
        f"- Tạo lúc (UTC): {created_at}",
        f"- Số nguồn đã đóng gói: {len(included)}",
        f"- Số nguồn không tải được: {len(failed)}",
        "",
        "## Cách đưa vào NotebookLM cá nhân",
        "",
        "1. Giải nén gói ZIP này vào một thư mục trên máy tính.",
        "2. Mở NotebookLM cá nhân tại https://notebooklm.google.com/ và tạo notebook theo bài học hoặc chủ đề.",
        "3. Dùng chức năng thêm nguồn của NotebookLM để chọn các tệp trong thư mục `sources/` phù hợp với notebook. ZIP này là gói trung chuyển, không phải một nguồn để tải nguyên ZIP lên NotebookLM.",
        "4. Đọc `SOURCE_INDEX.md` để kiểm tra môn, khối, năm học, mô tả và nguồn của từng tệp.",
        "5. Dùng các mẫu câu hỏi trong `NOTEBOOKLM_PROMPTS_VI.md` để khai thác tính năng gốc của NotebookLM như hỏi đáp theo nguồn, hướng dẫn học tập, câu hỏi ôn tập, sơ đồ tư duy và Audio Overview nếu giao diện tài khoản hỗ trợ.",
        "6. Đối chiếu câu trả lời với tài liệu gốc trước khi dùng trong dạy học hoặc phát cho học sinh.",
        "",
        "## Quy tắc nguồn",
        "",
        "- Các tệp trong `sources/` là bản sao tải về từ kho tài liệu hiện có; gói này không sửa hoặc xóa tệp gốc.",
        "- `manifest.json` chứa metadata và mã SHA-256 để kiểm tra tính toàn vẹn của tệp đã đóng gói.",
        "- Không đưa thông tin cá nhân nhạy cảm của học sinh vào notebook nếu không cần thiết và chưa được phép.",
        "- NotebookLM cá nhân không được điều khiển tự động bởi gói này; thao tác tạo notebook và thêm nguồn vẫn do giáo viên thực hiện trên giao diện NotebookLM.",
        "",
    ]
    if failed:
        lines += ["## Nguồn không tải được", "", "Các nguồn sau không được đưa vào gói; hãy kiểm tra quyền Google Drive hoặc kết nối rồi thử lại:", ""]
        lines += [f"- `{_markdown_cell(row.get('title'))}` (`{_markdown_cell(row.get('file_name'))}`, ID `{_markdown_cell(row.get('document_id'))}`) — {_markdown_cell(row.get('error'))}" for row in failed]
        lines.append("")
    if included:
        lines += ["## Nguồn trong gói", "", "| # | Tên tài liệu | Môn | Khối | Năm học | Tệp |", "|---:|---|---|---|---|---|"]
        for row in included:
            lines.append(
                f"| {row['sequence']} | {_markdown_cell(row['title'])} | {_markdown_cell(row['subject'])} | "
                f"{_markdown_cell(row['grade_level'])} | {_markdown_cell(row['academic_year'])} | `{_markdown_cell(row['archive_path'])}` |"
            )
        lines.append("")
    return "\n".join(lines)


def _prompts() -> str:
    return """# Mẫu câu lệnh tiếng Việt cho NotebookLM — giáo viên Toán THCS

Hãy chỉ sử dụng thông tin có trong nguồn đã thêm. Nếu nguồn không đủ căn cứ, hãy nói rõ chưa đủ thông tin và chỉ ra nguồn cần bổ sung. Phân biệt nguyên văn tài liệu với suy luận.

## 1. Tóm tắt bài học
Tóm tắt các nguồn theo cấu trúc: kiến thức trọng tâm, định nghĩa/tính chất, ví dụ mẫu, lỗi thường gặp, câu hỏi kiểm tra nhanh. Gắn tên nguồn cho từng ý quan trọng.

## 2. Chuẩn bị dạy học
Tạo dàn ý bài dạy Toán THCS từ các nguồn: mục tiêu, kiến thức tiên quyết, tiến trình, câu hỏi gợi mở, hoạt động học sinh, đánh giá nhanh. Không tự thêm chuẩn/chỉ tiêu nếu nguồn không nêu.

## 3. Phân hóa theo đối tượng
Tạo ba mức nhiệm vụ (cơ bản, đạt chuẩn, mở rộng) dựa trên nguồn. Với mỗi nhiệm vụ, nêu đáp án hoặc tiêu chí kiểm tra riêng ở phần dành cho giáo viên.

## 4. Tạo câu hỏi ôn tập
Tạo 10 câu hỏi từ dễ đến khó, bao gồm nhận biết, thông hiểu và vận dụng. Chỉ dùng nội dung nguồn; cung cấp lời giải và trỏ về nguồn hỗ trợ từng câu.

## 5. Phân tích sai lầm
Từ các ví dụ và bài tập trong nguồn, xác định lỗi học sinh có thể mắc, nguyên nhân, câu hỏi dẫn dắt để học sinh tự sửa và một bài tập tương tự.

## 6. Ma trận đối chiếu tài liệu
Lập bảng: chủ đề, kiến thức/ kỹ năng, nguồn dẫn chứng, dạng bài minh họa, nội dung còn thiếu hoặc mâu thuẫn. Không tự kết luận rằng tài liệu phù hợp quy định hiện hành nếu nguồn không chứng minh.

## 7. Tạo sơ đồ tư duy
Tạo sơ đồ tư duy phân cấp cho chủ đề; giữ đúng thuật ngữ và quan hệ toán học trong nguồn. Đánh dấu những nhánh chưa đủ tài liệu chứng minh.

## 8. Audio Overview
Tạo bản tổng quan âm thanh bằng tiếng Việt cho giáo viên/học sinh THCS, giải thích khái niệm và mối liên hệ dựa trên nguồn. Nêu rõ điểm cần kiểm tra lại, không biến suy luận thành dữ kiện.

## 9. Phiếu học tập
Tạo phiếu học tập ngắn gồm mục tiêu, nhiệm vụ, chỗ trống để học sinh làm, phần tự đánh giá và đáp án dành riêng cho giáo viên. Không tiết lộ đáp án trong phần học sinh.

## 10. Kiểm chứng
Kiểm tra câu trả lời/dàn ý sau đây đối chiếu với từng nguồn. Với mỗi nhận định, đánh dấu: có căn cứ, diễn giải hợp lý, mâu thuẫn nguồn, hoặc chưa có căn cứ; trích dẫn tên nguồn/đoạn liên quan khi có thể.
"""


def build_notebooklm_source_pack(
    documents: Iterable[TeacherDocument],
    download_document: DownloadDocument,
    *,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
    now: datetime | None = None,
) -> NotebookLMSourcePack:
    """Download teacher-selected documents and package source copies for NotebookLM.

    Individual download failures are reported in the bundle when at least one
    source succeeds. No catalog metadata or source file is modified/deleted.
    """
    if not callable(download_document):
        raise TypeError("download_document must be callable")
    if not isinstance(max_total_bytes, int) or isinstance(max_total_bytes, bool) or max_total_bytes <= 0:
        raise ValueError("max_total_bytes must be a positive integer")

    chosen = tuple(documents)
    if not chosen:
        raise NotebookLMSourcePackError("Hãy chọn ít nhất một tài liệu.")
    if len({item.document_id for item in chosen}) != len(chosen):
        raise NotebookLMSourcePackError("Danh sách có tài liệu bị chọn trùng.")

    timestamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
    created_at = timestamp.isoformat()
    pack_stamp = timestamp.strftime("%Y%m%d-%H%M%S")
    included: list[dict[str, object]] = []
    failed: list[dict[str, str]] = []
    content_by_path: list[tuple[str, bytes]] = []
    total_bytes = 0

    for index, document in enumerate(chosen, start=1):
        try:
            content = download_document(document)
            if not isinstance(content, bytes) or not content:
                raise ValueError("Tệp tải về rỗng hoặc không ở dạng bytes.")
            new_total = total_bytes + len(content)
            if new_total > max_total_bytes:
                raise ValueError(
                    f"Tổng dung lượng vượt giới hạn gói ({max_total_bytes / (1024 * 1024):.0f} MB). "
                    "Hãy giảm số tài liệu được chọn."
                )
            filename = _safe_filename(document.file_name)
            archive_path = f"sources/{index:03d}_{filename}"
            included.append(_metadata(document, index, archive_path, content))
            content_by_path.append((archive_path, content))
            total_bytes = new_total
        except Exception as error:
            failed.append({
                "document_id": document.document_id,
                "title": document.title,
                "file_name": document.file_name,
                "error": f"{type(error).__name__}: {str(error)[:500]}",
            })

    if not included:
        details = "; ".join(f"{row['title']}: {row['error']}" for row in failed[:3])
        raise NotebookLMSourcePackError("Không tải được tài liệu nào. " + details)

    manifest = {
        "schema_version": "1.0",
        "product": "MathTeacher AI NotebookLM Bridge",
        "target": "personal NotebookLM via manual source import",
        "created_at_utc": created_at,
        "included_count": len(included),
        "failed_count": len(failed),
        "total_source_bytes": total_bytes,
        "sources": included,
        "failed_sources": failed,
    }

    index_lines = [
        "# Chỉ mục nguồn NotebookLM", "",
        "Gói này giữ nguyên các bản sao nguồn đã chọn. Dùng tên tệp trong bảng để chọn nguồn khi nhập vào NotebookLM.",
        "", "| # | Tài liệu | Môn | Khối | Năm học | Loại | Tệp | SHA-256 |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for row in included:
        index_lines.append(
            f"| {row['sequence']} | {_markdown_cell(row['title'])} | {_markdown_cell(row['subject'])} | "
            f"{_markdown_cell(row['grade_level'])} | {_markdown_cell(row['academic_year'])} | "
            f"{_markdown_cell(row['category_label'])} | `{_markdown_cell(row['archive_path'])}` | `{row['sha256']}` |"
        )
    index_lines.append("")

    manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    csv_buffer = io.StringIO(newline="")
    fields = ["sequence", "title", "subject", "grade_level", "academic_year", "category_label", "file_name", "archive_path", "mime_type", "size_bytes", "sha256", "web_view_link", "description", "tags"]
    writer = csv.DictWriter(csv_buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in included:
        csv_row = dict(row)
        csv_row["tags"] = ", ".join(row["tags"])
        writer.writerow(csv_row)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for archive_path, content in content_by_path:
            archive.writestr(archive_path, content)
        archive.writestr("README_NOTEBOOKLM_VI.md", _readme(created_at, included, failed))
        archive.writestr("SOURCE_INDEX.md", "\n".join(index_lines))
        archive.writestr("source_manifest.json", manifest_json)
        archive.writestr("source_manifest.csv", csv_buffer.getvalue().encode("utf-8-sig"))
        archive.writestr("NOTEBOOKLM_PROMPTS_VI.md", _prompts())

    return NotebookLMSourcePack(
        filename=f"MathTeacherAI-NotebookLM-{pack_stamp}.zip",
        content=buffer.getvalue(),
        included_sources=tuple(included),
        failed_sources=tuple(failed),
    )
