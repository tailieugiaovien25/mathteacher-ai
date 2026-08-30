
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8-sig")

def test_teacher_portal_no_longer_exposes_global_template_setup():
    text = _read("scripts/teacher_portal/app.py")
    assert "lesson_plan_tab" not in text
    assert "render_lesson_plan_template_setup(" not in text

def test_teacher_information_and_assignment_tabs_remain():
    text = _read("scripts/teacher_portal/app.py")
    assert "information_tab, assignment_tab = st.tabs(" in text
    assert "_render_teacher_assignment_settings(" in text

def test_template_setup_module_is_preserved():
    text = _read("src/portal_v2/ui/lesson_plan_template_setup_streamlit.py")
    assert "def render_lesson_plan_template_setup(" in text
    assert "LessonPlanTemplateProfile" in text

def test_admin_runtime_bridge_remains_single_weekly_seam():
    text = _read("src/portal_v2/ui/weekly_schedule_streamlit.py")
    assert text.count("apply_active_admin_lesson_plan_configuration(") == 1

def test_user_operational_standardization_state_remains():
    text = _read("src/portal_v2/ui/weekly_schedule_streamlit.py")
    for token in (
        "standardization_subject_filter",
        "standardization_component_filter",
        "teaching_date",
        "week_number",
        "uploaded_content",
        "modification_plan",
        "lesson_standardization_teacher_user_id",
    ):
        assert token in text
