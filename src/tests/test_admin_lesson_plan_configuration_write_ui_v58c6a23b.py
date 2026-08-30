from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "src/portal_v2/ui/admin_lesson_plan_coordination_center_streamlit.py"


def _text():
    return UI.read_text(encoding="utf-8-sig")


def test_admin_write_foundation_is_wired_only_in_coordination_center():
    text = _text()
    assert "SupabaseLessonPlanConfigurationAdminRepository" in text
    assert "LessonPlanConfigurationAdminService" in text
    assert "def _render_admin_configuration_write_workspace" in text
    assert "_render_admin_configuration_write_workspace(st, client=client)" in text


def test_admin_write_actions_are_explicit_and_form_guarded():
    text = _text()
    for token in [
        "Tạo cấu hình và phiên bản nháp",
        "Tạo phiên bản DRAFT mới",
        "Lưu DRAFT",
        "Xuất bản PUBLISHED",
        "Đặt làm phiên bản hiện hành / ACTIVE",
    ]:
        assert token in text

    assert text.count("st.form_submit_button(") >= 5
    assert "st.checkbox(" in text


def test_payload_requires_json_object():
    text = _text()
    assert "def _parse_configuration_payload" in text
    assert "json.loads" in text
    assert "isinstance(payload, dict)" in text


def test_grouping_policy_remains_in_same_center():
    text = _text()
    assert "render_admin_lesson_plan_grouping_policy" in text
    assert 'st.subheader("Chính sách nhóm giáo án")' in text


def test_existing_read_runtime_remains_available():
    text = _text()
    assert "SupabaseLessonPlanConfigurationRepository" in text
    assert "LessonPlanConfigurationService" in text
    assert 'st.subheader("Cấu hình giáo án đang hoạt động")' in text
