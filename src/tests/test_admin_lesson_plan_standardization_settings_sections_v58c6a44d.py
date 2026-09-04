from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "portal_v2" / "ui" / "admin_lesson_plan_coordination_center_streamlit.py"

def _text() -> str:
    return UI.read_text(encoding="utf-8-sig")

def test_standardization_editor_has_four_visual_business_sections() -> None:
    text = _text()
    assert "### 1. Mẫu & trình bày" in text
    assert "### 2. Ngày soạn – ngày duyệt" in text
    assert "### 3. Phê duyệt" in text
    assert "### 4. Nâng cao" in text

def test_version_management_is_visually_secondary() -> None:
    text = _text()
    assert 'st.markdown("## Quản trị phiên bản")' in text
    assert "Khu vực kỹ thuật để lưu lịch sử thay đổi cấu hình" in text
    assert "Tạo phiên bản cấu hình mới" in text
    assert "Chỉnh sửa phiên bản đang soạn" in text
    assert "Xuất bản phiên bản để sử dụng" in text
    assert "Chọn phiên bản đang áp dụng" in text
    assert "Áp dụng phiên bản này" in text

def test_advanced_json_remains_collapsed() -> None:
    text = _text()
    assert 'with st.expander("Cấu hình nâng cao (JSON)", expanded=False):' in text
