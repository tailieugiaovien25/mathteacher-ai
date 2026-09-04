from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "portal_v2" / "ui" / "admin_lesson_plan_coordination_center_streamlit.py"

def _text() -> str:
    return UI.read_text(encoding="utf-8-sig")

def test_standardization_settings_has_explicit_business_heading() -> None:
    text = _text()
    assert 'st.subheader("Cài đặt công cụ Chuẩn hóa giáo án")' in text
    assert "mẫu trình bày, ngày soạn/ngày duyệt, khối phê duyệt" in text

def test_standardization_settings_explains_admin_user_boundary() -> None:
    text = _text()
    assert "Các thiết lập tại đây áp dụng cho USER" in text
    assert "không bị chuyển quyền sở hữu" in text

def test_create_configuration_uses_business_friendly_labels() -> None:
    text = _text()
    assert "Thiết lập cấu hình Chuẩn hóa giáo án mới" in text
    assert "Mã cấu hình (hệ thống)" in text
    assert "Tên cấu hình hiển thị" in text
