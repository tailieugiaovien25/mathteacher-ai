from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from io import BytesIO

import pytest

from notebooklm_bridge import NotebookLMSourcePackError, build_notebooklm_source_pack
from teacher_document_library_v2.models import DocumentCategory, TeacherDocument


def make_document(*, file_name: str = "Giao-an-bai-1.docx", document_id: str = "00000000-0000-0000-0000-000000000001") -> TeacherDocument:
    return TeacherDocument(
        document_id=document_id,
        title="Giáo án số học",
        category=DocumentCategory.LESSON_PLAN,
        academic_year="2026-2027",
        subject="Toán",
        grade_level="6",
        class_name="6A1",
        file_name=file_name,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=4,
        storage_provider="google_drive_oauth",
        storage_file_id="drive-file-1",
        web_view_link="https://drive.google.com/file/d/drive-file-1/view",
        description="Bài học số học cơ bản",
        tags=("số học", "mt_material_v1:book=Kết nối tri thức", "mt_material_v1:lesson=Bài 1"),
    )


def test_build_source_pack_includes_files_index_and_vietnamese_prompts():
    doc = make_document()
    pack = build_notebooklm_source_pack(
        [doc],
        lambda selected: b"fake-docx-bytes",
        now=datetime(2026, 10, 10, tzinfo=timezone.utc),
    )

    assert pack.filename.startswith("MathTeacherAI-NotebookLM-20261010-000000")
    assert len(pack.included_sources) == 1
    assert pack.included_sources[0]["sha256"] == hashlib.sha256(b"fake-docx-bytes").hexdigest()
    with zipfile.ZipFile(BytesIO(pack.content)) as archive:
        names = set(archive.namelist())
        assert "sources/001_Giao-an-bai-1.docx" in names
        assert "README_NOTEBOOKLM_VI.md" in names
        assert "SOURCE_INDEX.md" in names
        assert "source_manifest.json" in names
        assert "source_manifest.csv" in names
        assert "NOTEBOOKLM_PROMPTS_VI.md" in names
        assert archive.read("sources/001_Giao-an-bai-1.docx") == b"fake-docx-bytes"
        manifest = json.loads(archive.read("source_manifest.json"))
        assert manifest["included_count"] == 1
        assert manifest["sources"][0]["document_id"] == doc.document_id
        readme = archive.read("README_NOTEBOOKLM_VI.md").decode("utf-8")
        assert "giải nén" in readme.lower()
        assert "không phải một nguồn để tải nguyên ZIP" in readme
        prompts = archive.read("NOTEBOOKLM_PROMPTS_VI.md").decode("utf-8")
        assert "Audio Overview" in prompts


def test_source_names_cannot_escape_sources_directory():
    doc = make_document(file_name="../../secret.txt")
    pack = build_notebooklm_source_pack([doc], lambda selected: b"safe")
    with zipfile.ZipFile(BytesIO(pack.content)) as archive:
        source_names = [name for name in archive.namelist() if name.startswith("sources/")]
    assert len(source_names) == 1
    assert source_names[0] == "sources/001_secret.txt"
    assert all(".." not in name.split("/") for name in source_names)


def test_failed_source_is_reported_when_another_source_succeeds():
    first = make_document()
    second = make_document(
        file_name="matran.pdf",
        document_id="00000000-0000-0000-0000-000000000002",
    )

    def downloader(doc):
        if doc.document_id == second.document_id:
            raise PermissionError("Drive permission denied")
        return b"source"

    pack = build_notebooklm_source_pack([first, second], downloader)
    assert len(pack.included_sources) == 1
    assert len(pack.failed_sources) == 1
    assert "PermissionError" in pack.failed_sources[0]["error"]
    with zipfile.ZipFile(BytesIO(pack.content)) as archive:
        manifest = json.loads(archive.read("source_manifest.json"))
        assert manifest["failed_count"] == 1
        assert second.document_id in archive.read("README_NOTEBOOKLM_VI.md").decode("utf-8")


def test_all_downloads_fail_raises_clear_error():
    with pytest.raises(NotebookLMSourcePackError, match="Không tải được tài liệu nào"):
        build_notebooklm_source_pack([make_document()], lambda selected: (_ for _ in ()).throw(PermissionError("denied")))


def test_pack_rejects_empty_or_duplicate_selection_and_invalid_limit():
    doc = make_document()
    with pytest.raises(NotebookLMSourcePackError, match="ít nhất một"):
        build_notebooklm_source_pack([], lambda selected: b"x")
    with pytest.raises(NotebookLMSourcePackError, match="chọn trùng"):
        build_notebooklm_source_pack([doc, doc], lambda selected: b"x")
    with pytest.raises(ValueError, match="positive integer"):
        build_notebooklm_source_pack([doc], lambda selected: b"x", max_total_bytes=0)


def test_total_size_limit_is_enforced():
    one = make_document()
    two = make_document(document_id="00000000-0000-0000-0000-000000000002", file_name="b.pdf")
    pack = build_notebooklm_source_pack([one, two], lambda selected: b"12345", max_total_bytes=6)
    assert len(pack.included_sources) == 1
    assert len(pack.failed_sources) == 1
    assert "vượt giới hạn" in pack.failed_sources[0]["error"]
