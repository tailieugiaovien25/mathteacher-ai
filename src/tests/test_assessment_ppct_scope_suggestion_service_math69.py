import pytest

from assessment_generation_v2.services.assessment_ppct_scope_suggestion_service import (
    AssessmentPpctScopeSuggestionError,
    AssessmentPpctScopeSuggestionService,
)
from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)


def ppct_row(
    *,
    subject_grade: str,
    period: int,
    lesson_name: str | None = None,
    sub_subject: str | None = None,
) -> PPCTRow:
    return PPCTRow(
        subject_grade=subject_grade,
        period=period,
        lesson_name=(
            lesson_name
            or f"Bai hoc {period}"
        ),
        sub_subject=sub_subject,
    )


def math_rows(
    *,
    grade: int,
    marker_period: int,
    marker_title: str,
    subject_grade: str | None = None,
    sub_subject: str | None = None,
) -> tuple[PPCTRow, ...]:
    label = (
        subject_grade
        or f"Toan {grade}"
    )

    rows = [
        ppct_row(
            subject_grade=label,
            period=period,
            sub_subject=sub_subject,
        )
        for period in range(1, marker_period)
    ]

    rows.append(
        ppct_row(
            subject_grade=label,
            period=marker_period,
            lesson_name=marker_title,
            sub_subject=sub_subject,
        )
    )

    return tuple(rows)


def test_teacher_selection_auto_suggests_math8_midterm_s1_scope():
    rows = math_rows(
        grade=8,
        marker_period=37,
        marker_title="Kiểm tra giữa học kỳ I",
        subject_grade="Toán 8",
    )

    result = (
        AssessmentPpctScopeSuggestionService()
        .suggest(
            ppct_rows=rows,
            grade_level=8,
            assessment_type="MIDTERM",
            semester=1,
        )
    )

    assert result.period_from == 1
    assert result.period_to == 36
    assert result.marker_period == 37
    assert result.evidence_source == "PPCT"
    assert result.suggestion_status == "SUGGESTED_FROM_PPCT"


def test_scope_boundary_is_derived_not_hard_coded():
    rows = math_rows(
        grade=8,
        marker_period=31,
        marker_title="Kiem tra giua hoc ky I",
    )

    result = (
        AssessmentPpctScopeSuggestionService()
        .suggest(
            ppct_rows=rows,
            grade_level=8,
            assessment_type="MIDTERM",
            semester=1,
        )
    )

    assert result.period_to == 30


def test_only_selected_grade_scope_is_used():
    rows = (
        math_rows(
            grade=7,
            marker_period=29,
            marker_title="Kiem tra giua hoc ky I",
        )
        + math_rows(
            grade=8,
            marker_period=37,
            marker_title="Kiem tra giua hoc ky I",
        )
    )

    result = (
        AssessmentPpctScopeSuggestionService()
        .suggest(
            ppct_rows=rows,
            grade_level=8,
            assessment_type="MIDTERM",
            semester=1,
        )
    )

    assert result.subject_grade == "Toan 8"
    assert result.period_to == 36


def test_vietnamese_subject_name_matches_unaccented_ppct_scope():
    rows = math_rows(
        grade=8,
        marker_period=37,
        marker_title="Kiem tra giua hoc ky I",
        subject_grade="Toan 8",
    )

    result = (
        AssessmentPpctScopeSuggestionService()
        .suggest(
            ppct_rows=rows,
            grade_level=8,
            assessment_type="MIDTERM",
            semester=1,
            subject_name="Toán",
        )
    )

    assert result.period_to == 36


def test_missing_grade_scope_fails_closed():
    rows = math_rows(
        grade=7,
        marker_period=29,
        marker_title="Kiem tra giua hoc ky I",
    )

    with pytest.raises(
        AssessmentPpctScopeSuggestionError,
        match="no PPCT scope matches",
    ):
        (
            AssessmentPpctScopeSuggestionService()
            .suggest(
                ppct_rows=rows,
                grade_level=8,
                assessment_type="MIDTERM",
                semester=1,
            )
        )


def test_multiple_sub_subjects_without_selection_fail_closed():
    rows = (
        math_rows(
            grade=8,
            marker_period=20,
            marker_title="Kiem tra giua hoc ky I",
            sub_subject="Dai so",
        )
        + math_rows(
            grade=8,
            marker_period=18,
            marker_title="Kiem tra giua hoc ky I",
            sub_subject="Hinh hoc",
        )
    )

    with pytest.raises(
        AssessmentPpctScopeSuggestionError,
        match="ambiguous",
    ):
        (
            AssessmentPpctScopeSuggestionService()
            .suggest(
                ppct_rows=rows,
                grade_level=8,
                assessment_type="MIDTERM",
                semester=1,
            )
        )


def test_explicit_sub_subject_resolves_one_scope():
    rows = (
        math_rows(
            grade=8,
            marker_period=20,
            marker_title="Kiem tra giua hoc ky I",
            sub_subject="Dai so",
        )
        + math_rows(
            grade=8,
            marker_period=18,
            marker_title="Kiem tra giua hoc ky I",
            sub_subject="Hinh hoc",
        )
    )

    result = (
        AssessmentPpctScopeSuggestionService()
        .suggest(
            ppct_rows=rows,
            grade_level=8,
            assessment_type="MIDTERM",
            semester=1,
            sub_subject="Đại số",
        )
    )

    assert result.sub_subject == "Dai so"
    assert result.period_to == 19


def test_missing_exam_marker_propagates_fail_closed():
    rows = tuple(
        ppct_row(
            subject_grade="Toan 8",
            period=period,
        )
        for period in range(1, 37)
    )

    with pytest.raises(
        AssessmentPpctScopeSuggestionError,
        match="marker not found",
    ):
        (
            AssessmentPpctScopeSuggestionService()
            .suggest(
                ppct_rows=rows,
                grade_level=8,
                assessment_type="MIDTERM",
                semester=1,
            )
        )


def test_grade_must_be_6_to_9():
    rows = math_rows(
        grade=8,
        marker_period=37,
        marker_title="Kiem tra giua hoc ky I",
    )

    with pytest.raises(
        AssessmentPpctScopeSuggestionError,
        match="6, 7, 8, 9",
    ):
        (
            AssessmentPpctScopeSuggestionService()
            .suggest(
                ppct_rows=rows,
                grade_level=10,
                assessment_type="MIDTERM",
                semester=1,
            )
        )


def test_empty_ppct_rows_fail_closed():
    with pytest.raises(
        AssessmentPpctScopeSuggestionError,
        match="must not be empty",
    ):
        (
            AssessmentPpctScopeSuggestionService()
            .suggest(
                ppct_rows=(),
                grade_level=8,
                assessment_type="MIDTERM",
                semester=1,
            )
        )


def test_selection_key_is_stable_for_ui_change_detection():
    rows = math_rows(
        grade=8,
        marker_period=37,
        marker_title="Kiem tra giua hoc ky I",
    )

    result = (
        AssessmentPpctScopeSuggestionService()
        .suggest(
            ppct_rows=rows,
            grade_level=8,
            assessment_type="MIDTERM",
            semester=1,
        )
    )

    assert result.selection_key == (
        8,
        "MIDTERM",
        1,
        "Toan 8",
        None,
    )