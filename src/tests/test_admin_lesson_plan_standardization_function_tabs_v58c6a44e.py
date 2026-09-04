from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "portal_v2" / "ui" / "admin_lesson_plan_coordination_center_streamlit.py"

def _text() -> str:
    return UI.read_text(encoding="utf-8-sig")

def test_standardization_settings_exposes_selectable_function_tabs() -> None:
    text = _text()
    assert "### Danh sách chức năng cài đặt" in text
    assert "Chọn nhóm chức năng cần thiết lập cho công cụ Chuẩn hóa giáo án." in text
    assert "st.tabs(" in text
    for label in ["Mẫu & trình bày", "Ngày soạn – ngày duyệt", "Phê duyệt", "Nâng cao"]:
        assert label in text

def test_each_settings_domain_is_rendered_inside_a_tab() -> None:
    text = _text()
    assert "with presentation_tab:" in text
    assert "with date_tab:" in text
    assert "with approval_tab:" in text
    assert "with advanced_tab:" in text
