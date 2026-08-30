"""V57-C PHASE 1 tests."""
from portal_v2.context.legacy_session_context_adapter import (
    project_system_context, registered_legacy_keys, resolve_legacy_value,
)

def test_projects_without_mutation():
    state = {
        "portal_user_id": "teacher-1",
        "system_weekly_academic_year": "2026-2027",
        "system_weekly_week_number": 5,
        "standardization_authoring_week_number": 5,
        "standardization_subject_filter": "MATH",
        "standardization_component_filter": "ARITHMETIC",
    }
    before = dict(state)
    context = project_system_context(state)
    assert state == before
    assert context.user_id == "teacher-1"
    assert context.academic_year == "2026-2027"
    assert context.week_number == 5
    assert context.subject_ref == "MATH"
    assert context.component_ref == "ARITHMETIC"

def test_active_week_precedence():
    state = {
        "global_weekly_active_week_number": 7,
        "standardization_authoring_week_number": 6,
        "system_weekly_week_number": 5,
    }
    assert resolve_legacy_value(state, "week_number") == 7

def test_blank_alias_falls_through():
    state = {
        "global_weekly_active_academic_year": " ",
        "system_weekly_academic_year": "2026-2027",
    }
    assert resolve_legacy_value(state, "academic_year") == "2026-2027"

def test_invalid_numeric_falls_through():
    state = {
        "global_weekly_active_week_number": "bad",
        "system_weekly_week_number": "8",
    }
    assert resolve_legacy_value(state, "week_number") == 8

def test_registered_keys_cover_observed_seams():
    keys = registered_legacy_keys()
    assert {
        "portal_user_id",
        "system_weekly_academic_year",
        "system_weekly_week_number",
        "standardization_authoring_week_number",
        "standardization_subject_filter",
        "standardization_component_filter",
    } <= keys
