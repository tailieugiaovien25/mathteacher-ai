from pathlib import Path

from lesson_planning_v2.services.lesson_plan_configuration_runtime_bridge import (
    ADMIN_RUNTIME_PAYLOAD_KEY,
    project_admin_payload_to_standardization_state,
)

ROOT = Path(__file__).resolve().parents[2]

def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")

def test_date_policy_projects_only_existing_standardization_keys():
    state = {}
    payload = {
        "date_policy": {
            "drafting_before_monday_enabled": False,
            "drafting_before_monday_days": 3,
            "approval_before_monday_enabled": True,
            "approval_before_monday_days": 1,
            "unrelated_key": "must-not-project",
        },
        "template_profile": {"profile_name": "ADMIN"},
    }
    project_admin_payload_to_standardization_state(
        payload=payload, session_state=state
    )
    assert state["standardization_drafting_before_monday_enabled"] is False
    assert state["standardization_drafting_before_monday_days"] == 3
    assert state["standardization_approval_before_monday_enabled"] is True
    assert state["standardization_approval_before_monday_days"] == 1
    assert "unrelated_key" not in state
    assert state[ADMIN_RUNTIME_PAYLOAD_KEY]["template_profile"]["profile_name"] == "ADMIN"

def test_weekly_has_exactly_one_admin_runtime_bridge_call():
    weekly = _text("src/portal_v2/ui/weekly_schedule_streamlit.py")
    assert weekly.count("apply_active_admin_lesson_plan_configuration(") == 1
    assert weekly.count("def _render_lesson_plan_standardization_workspace(") == 1


def test_teacher_global_settings_are_now_admin_governed():
    teacher = _text("scripts/teacher_portal/app.py")
    assert "render_lesson_plan_template_setup(" not in teacher
    assert "lesson_plan_tab" not in teacher


def test_legacy_duplicate_counts_are_preserved():
    weekly = _text("src/portal_v2/ui/weekly_schedule_streamlit.py")
    assert weekly.count("def _render_standardization_control_panel") == 4
    assert weekly.count("def _process_lesson_plan_upload") == 4
