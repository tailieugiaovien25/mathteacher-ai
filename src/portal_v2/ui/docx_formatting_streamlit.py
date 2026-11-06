"""Streamlit interface for content-safe DOCX formatting."""
from __future__ import annotations

import re
import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from mathteacher_ai.document_transformation.docx_transformer import transform_docx


MAX_UPLOAD_BYTES = 25 * 1024 * 1024
DOCX_MIME = (
    "application/vnd.openxmlformats-officedocument."
    "wordprocessingml.document"
)


def _safe_output_name(file_name: str) -> str:
    stem = Path(file_name or "giao-an").stem
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-") or "giao-an"
    return f"{stem}_CHUAN_HOA.docx"


def _validate_docx_payload(payload: bytes) -> None:
    if not payload:
        raise ValueError("Tệp tải lên đang trống.")
    if len(payload) > MAX_UPLOAD_BYTES:
        raise ValueError("Tệp vượt quá giới hạn 25 MB.")
    with tempfile.SpooledTemporaryFile(max_size=MAX_UPLOAD_BYTES) as stream:
        stream.write(payload)
        stream.seek(0)
        if not zipfile.is_zipfile(stream):
            raise ValueError("Tệp không phải gói DOCX hợp lệ.")
        stream.seek(0)
        with zipfile.ZipFile(stream) as archive:
            names = set(archive.namelist())
            if "word/document.xml" not in names or "[Content_Types].xml" not in names:
                raise ValueError("Cấu trúc DOCX không đầy đủ.")


def render_docx_formatting_tool() -> None:
    """Render the formatting-only workflow inside the authenticated teacher portal."""
    st.subheader("Chuẩn hóa định dạng giáo án Word")
    st.caption(
        "Chuẩn hóa hình thức DOCX; không dùng AI để viết lại nội dung. "
        "Tệp gốc không bị ghi đè và không tự điền ngày dạy."
    )
    with st.expander("Các quy tắc định dạng", expanded=False):
        st.markdown(
            "- Khổ giấy A4; lề trên/dưới 2 cm, trái 3 cm, phải 2 cm.\n"
            "- Times New Roman, cỡ 14, màu chữ đen.\n"
            "- Thu gọn khoảng cách đoạn và lề trong ô bảng.\n"
            "- Bỏ highlight/shading và dòng WEEK: trong ô ngày của tiết học.\n"
            "- Giữ nguyên nội dung và ảnh nhúng; không ghi đè tệp nguồn."
        )
    uploaded = st.file_uploader(
        "Chọn giáo án Word (.docx)",
        type=("docx",),
        key="docx_formatting_upload_v1",
        help="Tối đa 25 MB. Hãy giữ lại bản gốc để đối chiếu.",
    )
    if uploaded is None:
        st.info("Tải lên một tệp DOCX để bắt đầu.")
        return

    payload = uploaded.getvalue()
    st.write(f"Tệp: **{uploaded.name}** · {len(payload) / 1024:.1f} KB")
    if not st.button(
        "Chuẩn hóa định dạng",
        key="docx_formatting_run_v1",
        type="primary",
        use_container_width=True,
    ):
        return

    try:
        _validate_docx_payload(payload)
        with tempfile.TemporaryDirectory(prefix="mathteacher-docx-") as work_dir:
            source_path = Path(work_dir) / "source.docx"
            output_path = Path(work_dir) / "formatted.docx"
            source_path.write_bytes(payload)
            transform_docx(source_path, output_path)
            result = output_path.read_bytes()

        st.success("Đã chuẩn hóa và kiểm tra tính toàn vẹn nội dung/ảnh nhúng.")
        st.info(
            "Chế độ hiện tại chỉ chuẩn hóa định dạng. Các trường ngày tháng "
            "được giữ theo tài liệu gốc; không tự suy đoán hoặc điền ngày."
        )
        st.download_button(
            "Tải giáo án đã chuẩn hóa",
            data=result,
            file_name=_safe_output_name(uploaded.name),
            mime=DOCX_MIME,
            key="docx_formatting_download_v1",
            use_container_width=True,
        )
    except (ValueError, FileNotFoundError, FileExistsError, zipfile.BadZipFile) as error:
        st.error(f"Không thể xử lý tệp: {error}")
    except Exception as error:
        st.error(
            "Quá trình chuẩn hóa chưa hoàn tất. Tệp gốc vẫn được giữ nguyên. "
            f"Chi tiết: {type(error).__name__}: {error}"
        )
