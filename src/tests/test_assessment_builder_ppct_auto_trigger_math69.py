import pytest

from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)
from portal_v2.ui import assessment_builder_streamlit as ui


class _FakeSt:
    def __init__(self, session_state=None):
        self.session_state = (
            {} if session_state is None else session_state
        )


def _rows(
    *,
    grade: int,
    marker_period: int,
    marker_title: str,
) -> tuple[PPCTRow, ...]:
    subject_grade = f"Toan {grade}"
    values = tuple(
        PPCTRow(
            subject_grade=subject_grade,
            period=period,
            lesson_name=f"Bai hoc {period}",
        )
        for period in range(1, marker_period)
    )

    return values + (
        PPCTRow(
            subject_grade=subject_grade,
            period=marker_period,
            lesson_name=marker_title,
        ),
    )


def test_session_ppct_rows_are_read_from_outer_runtime_boundary():
    rows = _rows(
        grade=8,
        marker_period=37,
        marker_title="Kiem tra giua hoc ky I",
    )

    result = ui._ppct_rows_from_session(
        _FakeSt(
            {
                ui._ASSESSMENT_PPCT_ROWS_SESSION_KEY: rows,
            }
        )
    )

    assert result == rows


def test_missing_session_ppct_rows_remain_unresolved():
    assert (
        ui._ppct_rows_from_session(
            _FakeSt()
        )
        is None
    )


def test_invalid_session_ppct_contract_fails_closed():
    with pytest.raises(
        TypeError,
        match="must be a tuple",
    ):
        ui._ppct_rows_from_session(
            _FakeSt(
                {
                    ui._ASSESSMENT_PPCT_ROWS_SESSION_KEY: [],
                }
            )
        )


def test_selection_change_can_trigger_math8_midterm_scope_suggestion():
    rows = _rows(
        grade=8,
        marker_period=37,
        marker_title="Kiem tra giua hoc ky I",
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
    assert suggestion.period_from == 1
    assert suggestion.period_to == 36
    assert suggestion.marker_period == 37


def test_changed_ppct_marker_changes_scope_without_ui_hard_code():
    rows = _rows(
        grade=8,
        marker_period=31,
        marker_title="Kiem tra giua hoc ky I",
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
    assert suggestion.period_to == 30


def test_missing_ppct_never_invents_scope():
    suggestion, error = (
        ui._automatic_ppct_scope_suggestion(
            ppct_rows=None,
            grade_level=8,
            assessment_type_code="MIDTERM",
            semester_number=1,
        )
    )

    assert suggestion is None
    assert error is not None
    assert "Không tự suy đoán" in error


def test_regular_assessment_does_not_force_ppct_boundary():
    suggestion, error = (
        ui._automatic_ppct_scope_suggestion(
            ppct_rows=None,
            grade_level=8,
            assessment_type_code="REGULAR",
            semester_number=1,
        )
    )

    assert suggestion is None
    assert error is None
