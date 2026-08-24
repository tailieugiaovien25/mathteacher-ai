from pathlib import Path


UI_FILE = Path(
    "src/portal_v2/ui/"
    "lesson_plan_template_setup_streamlit.py"
)


def source():
    return UI_FILE.read_text(
        encoding="utf-8-sig"
    )


def test_setup_page_has_template_title():
    text = source()

    assert (
        '"M\\u1eabu gi\\u00e1o \\u00e1n"'
        in text
        or '"M?u gi?o ?n"' in text
    )

def test_setup_page_has_structure_editor():
    text = source()

    assert "st.data_editor(" in text
    assert "Cấu trúc và đề mục" in text


def test_setup_page_has_header_settings():
    text = source()

    assert "Đầu giáo án" in text
    assert "Tiết in đậm" in text
    assert "Tên bài viết HOA" in text
    assert "Tên bài in đậm" in text


def test_setup_page_has_word_layout():
    text = source()

    assert "Định dạng Word" in text
    assert "Times New Roman" not in text
    assert "Font chung" in text
    assert "Cỡ chữ chung" in text
    assert "Lề trang" in text


def test_setup_page_has_scheduling_policy():
    text = source()

    assert "Ngày soạn mặc định" in text
    assert "Ngày duyệt sau Ngày soạn" in text
    assert "Lịch báo giảng" in text


def test_setup_page_supports_projected_schedule():
    text = source()

    assert (
        "Cho phép suy ra lịch dạy tuần kế tiếp"
        in text
    )

    assert (
        "Số tuần tối đa được suy ra"
        in text
    )


def test_setup_page_has_approval_settings():
    text = source()

    assert "Phê duyệt cuối giáo án" in text
    assert "Tổ CM duyệt" in text
    assert "Nhãn phê duyệt" in text
    assert "Số dòng trống" in text


def test_setup_page_can_save_and_reset():
    text = source()

    assert "Lưu Mẫu giáo án" in text
    assert "Khôi phục mẫu mặc định" in text
    assert "SESSION_KEY" in text


def test_setup_page_supports_embedding_in_teacher_settings():
    text = source()

    assert "embedded: bool = False" in text
    assert "if not embedded:" in text


def test_setup_page_labels_new_selection_modes_safely():
    text = source()

    assert "def _selection_mode_label(" in text
    assert "SELECTION_MODE_LABELS.get(" in text
    assert '"week_subject": "Theo tuần và môn"' in text
    assert "SELECTION_MODE_LABELS[item]" not in text
