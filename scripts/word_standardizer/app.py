"""Local web interface for the Lesson Plan Word Standardizer."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from document_standardization import LessonPlanWordStandardizer


APP_DIR = Path(__file__).resolve().parent
DEFAULT_PROFILE = APP_DIR / "lesson_plan_profile.json"
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def standardize_uploaded_docx(
    content: bytes, original_name: str, profile_path: Path = DEFAULT_PROFILE
) -> tuple[str, bytes, str, bytes, dict[str, object]]:
    """Standardize uploaded DOCX bytes and return downloadable artifacts."""
    safe_name = Path(original_name).name
    if not safe_name.lower().endswith(".docx"):
        raise ValueError("Chỉ chấp nhận tệp Word định dạng .docx.")
    if not content:
        raise ValueError("Tệp tải lên đang rỗng.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("Tệp vượt quá giới hạn 50 MB.")

    output_name = f"{Path(safe_name).stem}.standardized.docx"
    report_name = f"{Path(safe_name).stem}.standardization-report.json"
    with tempfile.TemporaryDirectory(prefix="mathteacher_word_") as temporary:
        workspace = Path(temporary)
        source = workspace / safe_name
        output = workspace / output_name
        report_path = workspace / report_name
        source.write_bytes(content)
        report = LessonPlanWordStandardizer.from_json(profile_path).standardize(
            source, output, report_path
        )
        return (
            output_name,
            output.read_bytes(),
            report_name,
            report_path.read_bytes(),
            report,
        )


def main(*, embedded: bool = False) -> None:
    import streamlit as st

    if not embedded:
        st.set_page_config(
            page_title="Chuẩn hóa kế hoạch bài dạy",
            page_icon="📘",
            layout="centered",
        )
    st.markdown(
        """
        <style>
        .block-container {max-width: 880px; padding-top: 2rem;}
        [data-testid="stFileUploaderDropzone"] {border: 2px dashed #2f6fed;}
        .result-box {padding: 1rem; border-radius: .75rem; background: #eef7ee;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    if not embedded:
        st.title("Chuẩn hóa kế hoạch bài dạy")
        st.caption("MathTeacher-AI V2 · Xử lý an toàn trên máy tính, không ghi đè bản gốc")

    with st.expander("Quy tắc chuẩn hóa đang áp dụng", expanded=False):
        st.markdown(
            """
            - Times New Roman, cỡ 14 trong và ngoài bảng.
            - Giữ cấu trúc công thức toán và chuẩn hóa phông công thức.
            - Điều chỉnh bảng theo khổ trang, cho phép hàng dài tiếp tục qua trang.
            - Xóa đầu/chân trang cũ và đánh số trang tự động ở giữa chân trang.
            """
        )

    uploaded = st.file_uploader(
        "Tải giáo án Word lên",
        type=["docx"],
        help="Tệp tối đa 50 MB. Tệp gốc không bị thay đổi.",
    )
    if uploaded is None:
        st.info("Chọn một tệp .docx để bắt đầu.")
        return

    st.write(f"**Đã chọn:** {uploaded.name} · {uploaded.size / 1024:.1f} KB")
    if st.button("Chuẩn hóa giáo án", type="primary", use_container_width=True):
        try:
            with st.spinner("Đang chuẩn hóa tài liệu..."):
                result = standardize_uploaded_docx(uploaded.getvalue(), uploaded.name)
                st.session_state["standardized_result"] = result
                st.session_state["standardized_source"] = uploaded.name
        except Exception as error:
            st.error(f"Không thể chuẩn hóa: {error}")

    result = st.session_state.get("standardized_result")
    if not result or st.session_state.get("standardized_source") != uploaded.name:
        return

    output_name, output_bytes, report_name, report_bytes, report = result
    before, changes = report["before"], report["changes"]
    st.markdown('<div class="result-box"><b>Chuẩn hóa hoàn tất.</b></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Đoạn văn", before["paragraphs"])
    col2.metric("Bảng", before["tables"])
    col3.metric("Công thức", before["omml_equations"])
    st.caption(
        f"Đã xử lý {changes.get('sections_normalized', 0)} phần tài liệu; "
        f"giữ nguyên {before['images']} hình ảnh."
    )
    st.download_button(
        "Tải bản Word đã chuẩn hóa",
        data=output_bytes,
        file_name=output_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
        use_container_width=True,
    )
    st.download_button(
        "Tải báo cáo kỹ thuật (JSON)",
        data=report_bytes,
        file_name=report_name,
        mime="application/json",
        use_container_width=True,
    )
    if report["result"] == "completed_with_review":
        st.warning("Hãy mở bản Word và kiểm tra trực quan công thức, bảng và ngắt trang trước khi sử dụng.")


if __name__ == "__main__":
    main()
