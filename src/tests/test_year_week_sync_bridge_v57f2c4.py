from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from portal_v2.context.models import SystemContext
from portal_v2.context.year_week_sync_bridge import (
    ACADEMIC_YEAR_ALIAS_KEYS,
    WEEK_NUMBER_ALIAS_KEYS,
    YearWeekContextBridge,
    project_year_week_aliases,
)

class RecordingService:
    def __init__(self):
        self.calls = []

    def apply_change(self, *, current, change):
        self.calls.append((current, change))
        updated = replace(current, **{change.field: change.value})
        return SimpleNamespace(context=updated, events=("recorded",))

def _context():
    return SystemContext(
        user_id="user-a",
        academic_year="2026-2027",
        week_number=1,
    )

def test_projection_covers_all_known_year_week_aliases():
    projection = project_year_week_aliases(_context())
    assert set(ACADEMIC_YEAR_ALIAS_KEYS).issubset(projection)
    assert set(WEEK_NUMBER_ALIAS_KEYS).issubset(projection)
    assert projection["global_weekly_active_academic_year"] == "2026-2027"
    assert projection["global_weekly_active_week_number"] == 1
    assert projection["standardization_authoring_week_number"] == 1
    assert projection["system_weekly_week_number"] == 1
    assert projection["lbg_user_week_number"] == 1

def test_week_change_is_emitted_as_context_change_before_projection():
    service = RecordingService()
    outcome = YearWeekContextBridge(service=service).apply_change(
        current=_context(),
        field="week_number",
        value=2,
        source_page="admin_context_control_center",
        source_control="week_number",
    )
    _, change = service.calls[0]
    assert change.field == "week_number"
    assert change.value == 2
    assert change.source_page == "admin_context_control_center"
    assert change.source_control == "week_number"
    assert outcome.context.week_number == 2
    assert all(outcome.projection[key] == 2 for key in WEEK_NUMBER_ALIAS_KEYS)

def test_academic_year_change_projects_to_both_legacy_aliases():
    service = RecordingService()
    outcome = YearWeekContextBridge(service=service).apply_change(
        current=_context(),
        field="academic_year",
        value="2027-2028",
        source_page="admin_context_control_center",
        source_control="academic_year",
    )
    assert outcome.context.academic_year == "2027-2028"
    assert all(
        outcome.projection[key] == "2027-2028"
        for key in ACADEMIC_YEAR_ALIAS_KEYS
    )

def test_bridge_rejects_non_year_week_fields():
    service = RecordingService()
    with pytest.raises(ValueError):
        YearWeekContextBridge(service=service).apply_change(
            current=_context(),
            field="subject_ref",
            value="math",
            source_page="test",
            source_control="subject",
        )
    assert service.calls == []

def test_bridge_module_contains_no_streamlit_session_state_writer():
    from portal_v2.context import year_week_sync_bridge as module
    source = Path(module.__file__).read_text(encoding="utf-8-sig")
    assert "st.session_state" not in source
    assert "import streamlit" not in source.lower()

def test_projection_does_not_mutate_context():
    current = _context()
    projection = project_year_week_aliases(current)
    projection["global_weekly_active_week_number"] = 99
    assert current.week_number == 1
