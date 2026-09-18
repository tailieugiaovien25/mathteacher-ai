from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)
from portal_v2.ui import assessment_builder_streamlit as ui


class _FakeSt:
    def __init__(self):
        self.session_state = {}


def _suggestion(marker_period: int):
    rows = tuple(
        PPCTRow(
            subject_grade="Toan 8",
            period=period,
            lesson_name=f"Bai hoc {period}",
        )
        for period in range(1, marker_period)
    ) + (
        PPCTRow(
            subject_grade="Toan 8",
            period=marker_period,
            lesson_name="Kiem tra giua hoc ky I",
        ),
    )

    suggestion, error = (
        ui._automatic_ppct_scope_suggestion(
            ppct_rows=rows,
            grade_level=8,
            assessment_type_code="MIDTERM",
            semester_number=1,
        )
    )

    assert error is None
    assert suggestion is not None

    return suggestion


def test_confirmation_is_false_before_teacher_confirms():
    st = _FakeSt()
    suggestion = _suggestion(37)

    assert not ui._ppct_scope_is_confirmed(
        st=st,
        suggestion=suggestion,
    )


def test_teacher_confirmation_is_bound_to_current_ppct_evidence():
    st = _FakeSt()
    suggestion = _suggestion(37)

    ui._confirm_ppct_scope(
        st=st,
        suggestion=suggestion,
    )

    assert ui._ppct_scope_is_confirmed(
        st=st,
        suggestion=suggestion,
    )


def test_changed_ppct_scope_invalidates_previous_confirmation():
    st = _FakeSt()
    original = _suggestion(37)
    changed = _suggestion(31)

    ui._confirm_ppct_scope(
        st=st,
        suggestion=original,
    )

    assert not ui._ppct_scope_is_confirmed(
        st=st,
        suggestion=changed,
    )


def test_clear_confirmation_removes_confirmation_state():
    st = _FakeSt()
    suggestion = _suggestion(37)

    ui._confirm_ppct_scope(
        st=st,
        suggestion=suggestion,
    )
    ui._clear_ppct_scope_confirmation(
        st=st,
    )

    assert not ui._ppct_scope_is_confirmed(
        st=st,
        suggestion=suggestion,
    )


def test_confirmation_token_changes_when_ppct_content_changes():
    original = _suggestion(37)

    changed_rows = list(original.scope_rows)
    changed_rows[0] = PPCTRow(
        subject_grade=changed_rows[0].subject_grade,
        period=changed_rows[0].period,
        lesson_name="Bai hoc 1 da cap nhat",
        sub_subject=changed_rows[0].sub_subject,
    )

    changed = type(original)(
        grade_level=original.grade_level,
        subject_name=original.subject_name,
        subject_grade=original.subject_grade,
        sub_subject=original.sub_subject,
        assessment_type=original.assessment_type,
        semester=original.semester,
        period_from=original.period_from,
        period_to=original.period_to,
        marker_period=original.marker_period,
        marker_title=original.marker_title,
        scope_rows=tuple(changed_rows),
        evidence_source=original.evidence_source,
        suggestion_status=original.suggestion_status,
    )

    assert (
        ui._ppct_scope_confirmation_token(
            original
        )
        != ui._ppct_scope_confirmation_token(
            changed
        )
    )
