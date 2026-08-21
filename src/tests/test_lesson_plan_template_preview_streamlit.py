from pathlib import Path


UI_FILE = Path(
    "src/portal_v2/ui/"
    "lesson_plan_template_setup_streamlit.py"
)


def source() -> str:
    return UI_FILE.read_text(
        encoding="utf-8"
    )


def test_template_setup_has_visual_preview():
    text = source()

    assert "Xem trước Mẫu giáo án" in text
    assert "_render_template_preview" in text


def test_preview_contains_header_structure():
    text = source()

    assert "Ngày soạn:" in text
    assert "Ngày dạy:" in text
    assert "Lớp 6A1" in text
    assert "Lớp 6A2" in text


def test_preview_contains_lesson_identity():
    text = source()

    assert "TIẾT 10 + 11" in text
    assert (
        "BÀI 7. THỨ TỰ THỰC HIỆN "
        "CÁC PHÉP TÍNH"
        in text
    )


def test_preview_contains_standard_sections():
    text = source()

    assert "I. MỤC TIÊU" in text
    assert (
        "II. THIẾT BỊ DẠY HỌC "
        "VÀ HỌC LIỆU"
        in text
    )
    assert "III. TIẾN TRÌNH DẠY HỌC" in text


def test_preview_contains_approval_block():
    text = source()

    assert "Ngày 26 tháng 10 năm 2026" in text
    assert "Tổ CM duyệt" in text


def test_preview_is_visual_html():
    text = source()

    assert "st.markdown(" in text
    assert "unsafe_allow_html=True" in text
    assert "lesson-plan-preview" in text
