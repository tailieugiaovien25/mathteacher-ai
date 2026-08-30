from pathlib import Path

from portal_v2.ui.admin_context_control_center_streamlit import build_admin_context_control_rows
from portal_v2.ui.admin_navigation import ADMIN_PAGE_CONTEXT_CONTROL_CENTER, admin_portal_page_ids


def test_admin_navigation_contains_context_control_center():
    assert ADMIN_PAGE_CONTEXT_CONTROL_CENTER == "context_control_center"
    assert ADMIN_PAGE_CONTEXT_CONTROL_CENTER in admin_portal_page_ids()


def test_rows_are_registry_driven_and_read_only():
    state = {
        "global_weekly_active_week_number": 2,
        "standardization_authoring_week_number": 2,
        "system_weekly_week_number": 2,
        "lbg_user_week_number": 2,
    }
    before = dict(state)
    rows = build_admin_context_control_rows(session_state=state)
    assert state == before
    assert any(row["canonical_field"] == "week_number" for row in rows)


def test_conflicting_week_aliases_are_visible():
    rows = build_admin_context_control_rows(session_state={
        "global_weekly_active_week_number": 2,
        "standardization_authoring_week_number": 1,
        "system_weekly_week_number": 2,
    })
    week = next(row for row in rows if row["canonical_field"] == "week_number")
    assert week["status"] == "CONFLICT"


def test_matching_week_aliases_are_ok():
    rows = build_admin_context_control_rows(session_state={
        "global_weekly_active_week_number": 2,
        "standardization_authoring_week_number": 2,
        "system_weekly_week_number": 2,
        "lbg_user_week_number": 2,
    })
    week = next(row for row in rows if row["canonical_field"] == "week_number")
    assert week["status"] == "OK"


def test_page_has_no_database_write_calls():
    path = Path(__file__).resolve().parents[1] / "portal_v2/ui/admin_context_control_center_streamlit.py"
    text = path.read_text(encoding="utf-8-sig")
    for token in (".save(", ".upsert(", ".insert(", ".update(", ".delete("):
        assert token not in text
