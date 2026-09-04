from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "portal_v2" / "ui" / "admin_lesson_authoring_ai_settings_streamlit.py"
CENTER = ROOT / "portal_v2" / "ui" / "admin_lesson_plan_coordination_center_streamlit.py"

def test_ai_settings_panel_has_five_business_tabs() -> None:
    text = MODULE.read_text(encoding="utf-8-sig")
    assert "Cài đặt công cụ Soạn bài cùng AI" in text
    assert "Danh sách chức năng cài đặt" in text
    for token in ["1. Thông tin chung", "2. AI & Nội dung", "3. Định dạng & Trình bày", "4. Tích hợp & Dữ liệu", "5. Nâng cao"]:
        assert token in text

def test_ai_settings_panel_has_preview_restore_and_save_actions() -> None:
    text = MODULE.read_text(encoding="utf-8-sig")
    assert "Xem trước hiển thị cho USER" in text
    assert "Khôi phục mặc định" in text
    assert "Lưu thiết lập" in text

def test_ai_settings_panel_is_wired_to_coordination_center() -> None:
    text = CENTER.read_text(encoding="utf-8-sig")
    assert "render_admin_lesson_authoring_ai_settings" in text
