from __future__ import annotations

from portal_v2.context.session_scoped_context_holder import (
    apply_canonical_year_week_change,
    ensure_canonical_context,
    get_canonical_context,
)


def _state() -> dict:
    return {
        "portal_user_id": "teacher-1",
        "global_weekly_active_academic_year": "2026-2027",
        "global_weekly_active_week_number": 1,
        "system_weekly_week_number": 1,
        "lbg_user_week_number": 1,
        "standardization_authoring_week_number": 1,
    }


def test_bootstrap_creates_stable_session_scoped_context():
    state = _state()
    identity1, context1 = ensure_canonical_context(
        state,
        user_id="teacher-1",
        source_page="weekly_schedule",
    )
    identity2, context2 = ensure_canonical_context(
        state,
        user_id="teacher-1",
        source_page="weekly_schedule",
    )
    assert identity1 == identity2
    assert context1 == context2
    assert context1.user_id == "teacher-1"
    assert context1.week_number == 1


def test_week_change_updates_canonical_then_projects_all_aliases():
    state = _state()
    updated = apply_canonical_year_week_change(
        state,
        user_id="teacher-1",
        field="week_number",
        value=2,
        source_page="standardization",
        source_control="standardization_authoring_week_number",
    )
    assert updated.week_number == 2
    assert updated.context_version == 1
    assert state["global_weekly_active_week_number"] == 2
    assert state["system_weekly_week_number"] == 2
    assert state["lbg_user_week_number"] == 2
    assert state["standardization_authoring_week_number"] == 2


def test_academic_year_change_projects_both_year_aliases():
    state = _state()
    updated = apply_canonical_year_week_change(
        state,
        user_id="teacher-1",
        field="academic_year",
        value="2027-2028",
        source_page="weekly_schedule",
        source_control="system_weekly_academic_year",
    )
    assert updated.academic_year == "2027-2028"
    assert state["global_weekly_active_academic_year"] == "2027-2028"
    assert state["system_weekly_academic_year"] == "2027-2028"


def test_rejects_non_year_week_field():
    state = _state()
    try:
        apply_canonical_year_week_change(
            state,
            user_id="teacher-1",
            field="subject_ref",
            value="MATH",
            source_page="weekly_schedule",
            source_control="subject",
        )
    except ValueError as error:
        assert "Unsupported canonical year/week field" in str(error)
    else:
        raise AssertionError("expected ValueError")


def test_different_session_state_gets_different_context_identity():
    state1 = _state()
    state2 = _state()
    identity1, _ = ensure_canonical_context(
        state1,
        user_id="teacher-1",
        source_page="weekly_schedule",
    )
    identity2, _ = ensure_canonical_context(
        state2,
        user_id="teacher-1",
        source_page="weekly_schedule",
    )
    assert identity1.context_id != identity2.context_id


def test_get_returns_latest_canonical_context_not_reprojected_legacy_value():
    state = _state()
    apply_canonical_year_week_change(
        state,
        user_id="teacher-1",
        field="week_number",
        value=3,
        source_page="lbg",
        source_control="system_weekly_week_number",
    )
    state["lbg_user_week_number"] = 1
    current = get_canonical_context(
        state,
        user_id="teacher-1",
        source_page="weekly_schedule",
    )
    assert current.week_number == 3
