from pathlib import Path

from lesson_planning_v2.services.lesson_plan_configuration_runtime_bridge import (
    project_admin_payload_to_standardization_state,
)

ROOT = Path(__file__).resolve().parents[2]

def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")

def test_template_profile_projects_without_date_policy():
    state = {}
    payload = {
        "template_profile": {
            "profile_name": "ADMIN THCS",
            "layout": {"font_name": "Times New Roman"},
        }
    }
    project_admin_payload_to_standardization_state(
        payload=payload, session_state=state
    )
    assert state["lesson_plan_admin_template_profile"]["profile_name"] == "ADMIN THCS"
    assert state["lesson_plan_template_profile"]["layout"]["font_name"] == "Times New Roman"
    assert state["subject_lesson_plan_profile"]["profile_name"] == "ADMIN THCS"

def test_approval_policy_projects_without_date_policy():
    state = {}
    payload = {
        "approval_policy": {
            "approval_label": "T\u1ed5 CM duy\u1ec7t",
            "alignment": "RIGHT",
            "approval_offset_days": 1,
            "unrelated": "ignore",
        }
    }
    project_admin_payload_to_standardization_state(
        payload=payload, session_state=state
    )
    assert state["lesson_plan_admin_approval_label"] == "T\u1ed5 CM duy\u1ec7t"
    assert state["lesson_plan_admin_approval_alignment"] == "RIGHT"
    assert state["standardization_approval_before_monday_days"] == 1
    assert "unrelated" not in state

def test_all_three_sections_can_project_together():
    state = {}
    payload = {
        "date_policy": {"drafting_before_monday_days": 3},
        "template_profile": {"profile_name": "ADMIN"},
        "approval_policy": {"approval_offset_days": 1},
    }
    project_admin_payload_to_standardization_state(
        payload=payload, session_state=state
    )
    assert state["standardization_drafting_before_monday_days"] == 3
    assert state["lesson_plan_template_profile"]["profile_name"] == "ADMIN"
    assert state["standardization_approval_before_monday_days"] == 1

def test_absent_sections_do_not_overwrite_existing_state():
    state = {
        "lesson_plan_template_profile": {"profile_name": "EXISTING"},
        "lesson_plan_admin_approval_label": "EXISTING",
    }
    payload = {"date_policy": {"drafting_before_monday_days": 3}}
    project_admin_payload_to_standardization_state(
        payload=payload, session_state=state
    )
    assert state["lesson_plan_template_profile"]["profile_name"] == "EXISTING"
    assert state["lesson_plan_admin_approval_label"] == "EXISTING"

def test_weekly_still_has_exactly_one_admin_bridge_call():
    weekly = _text("src/portal_v2/ui/weekly_schedule_streamlit.py")
    assert weekly.count("apply_active_admin_lesson_plan_configuration(") == 1
    assert weekly.count("def _render_lesson_plan_standardization_workspace(") == 1


def test_teacher_global_template_settings_are_hidden_after_runtime_mapping():
    teacher = _text("scripts/teacher_portal/app.py")
    assert "render_lesson_plan_template_setup(" not in teacher
    assert "lesson_plan_tab" not in teacher
