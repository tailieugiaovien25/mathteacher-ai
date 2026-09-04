from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = ROOT / (
    "src/lesson_planning_v2/adapters/"
    "supabase_lesson_plan_configuration_admin_repository.py"
)
UI = ROOT / (
    "src/portal_v2/ui/admin_lesson_plan_coordination_center_streamlit.py"
)


def test_admin_repository_lists_profiles_for_selector_ui():
    text = REPOSITORY.read_text(encoding="utf-8-sig")
    assert "def list_profiles(self)" in text
    assert '.order("profile_name")' in text


def test_admin_ux_uses_profile_and_version_selectors():
    text = UI.read_text(encoding="utf-8-sig")

    assert "Chọn cấu hình cần quản lý" in text
    assert "Tạo từ phiên bản" in text
    assert "Chọn phiên bản DRAFT" in text
    assert "Chọn phiên bản DRAFT cần xuất bản" in text
    assert "Chọn phiên bản PUBLISHED" in text
    assert text.count("st.selectbox(") >= 5


def test_admin_ux_no_longer_requires_manual_ids_for_main_flow():
    text = UI.read_text(encoding="utf-8-sig")

    assert '"Profile ID"' not in text
    assert '"Configuration Version ID cần xuất bản"' not in text
    assert '"Configuration Version ID PUBLISHED"' not in text


def test_raw_json_is_demoted_to_advanced_configuration():
    text = UI.read_text(encoding="utf-8-sig")

    assert "Cấu hình nâng cao (JSON)" in text
    assert "JSON nâng cao" in text
    assert "Các trường trực quan phía trên sẽ được" in text


def test_safe_lifecycle_actions_remain():
    text = UI.read_text(encoding="utf-8-sig")

    assert "Tạo phiên bản DRAFT mới" in text
    assert "Lưu DRAFT" in text
    assert "Xuất bản PUBLISHED" in text
    assert "Áp dụng phiên bản này" in text
    assert "retire_previous=retire_previous" in text
