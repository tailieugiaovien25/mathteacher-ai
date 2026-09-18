import pytest

from assessment_generation_v2.services.assessment_ppct_scope_resolver import (
    AssessmentPpctScopeResolutionError,
    AssessmentPpctScopeResolver,
)
from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)


def row(
    period: int,
    title: str | None = None,
    *,
    subject_grade: str = "Toan 8",
    sub_subject: str | None = None,
) -> PPCTRow:
    return PPCTRow(
        subject_grade=subject_grade,
        period=period,
        lesson_name=title or f"Bai hoc {period}",
        sub_subject=sub_subject,
    )


def rows_with_marker(
    *,
    marker_period: int,
    marker_title: str,
    start: int = 1,
) -> tuple[PPCTRow, ...]:
    values = [
        row(period)
        for period in range(start, marker_period)
    ]
    values.append(
        row(
            marker_period,
            marker_title,
        )
    )
    return tuple(values)


def test_midterm_semester1_derives_1_to_36_from_ppct_marker():
    result = AssessmentPpctScopeResolver().resolve(
        rows=rows_with_marker(
            marker_period=37,
            marker_title="Kiem tra giua hoc ki I",
        ),
        assessment_type="MIDTERM",
        semester=1,
    )

    assert result.period_from == 1
    assert result.period_to == 36
    assert result.marker_period == 37


def test_scope_is_not_hard_coded_to_36():
    result = AssessmentPpctScopeResolver().resolve(
        rows=rows_with_marker(
            marker_period=31,
            marker_title="Kiem tra giua hoc ky 1",
        ),
        assessment_type="MIDTERM",
        semester=1,
    )

    assert result.period_from == 1
    assert result.period_to == 30


def test_vietnamese_diacritics_are_normalized():
    result = AssessmentPpctScopeResolver().resolve(
        rows=rows_with_marker(
            marker_period=37,
            marker_title="Kiểm tra giữa học kỳ I",
        ),
        assessment_type="midterm",
        semester=1,
    )

    assert result.period_to == 36


def test_final_semester1_uses_all_prior_semester1_periods():
    values = list(
        rows_with_marker(
            marker_period=72,
            marker_title="Kiem tra cuoi hoc ky I",
        )
    )
    values[36] = row(
        37,
        "Kiem tra giua hoc ky I",
    )

    result = AssessmentPpctScopeResolver().resolve(
        rows=tuple(values),
        assessment_type="FINAL",
        semester=1,
    )

    assert result.period_from == 1
    assert result.period_to == 71
    assert result.marker_period == 72


def test_midterm_semester2_starts_after_final_semester1_marker():
    values = [
        row(period)
        for period in range(1, 72)
    ]
    values.append(
        row(
            72,
            "Kiem tra cuoi hoc ky I",
        )
    )
    values.extend(
        row(period)
        for period in range(73, 104)
    )
    values.append(
        row(
            104,
            "Kiem tra giua hoc ky II",
        )
    )

    result = AssessmentPpctScopeResolver().resolve(
        rows=tuple(values),
        assessment_type="MIDTERM",
        semester=2,
    )

    assert result.period_from == 73
    assert result.period_to == 103
    assert result.marker_period == 104


def test_final_semester2_starts_after_final_semester1_marker():
    values = [
        row(period)
        for period in range(1, 72)
    ]
    values.append(
        row(
            72,
            "Kiem tra cuoi hoc ky I",
        )
    )
    values.extend(
        row(period)
        for period in range(73, 140)
    )
    values.append(
        row(
            140,
            "Kiem tra cuoi hoc ky II",
        )
    )

    result = AssessmentPpctScopeResolver().resolve(
        rows=tuple(values),
        assessment_type="FINAL",
        semester=2,
    )

    assert result.period_from == 73
    assert result.period_to == 139


def test_missing_target_marker_fails_closed():
    with pytest.raises(
        AssessmentPpctScopeResolutionError,
        match="marker not found",
    ):
        AssessmentPpctScopeResolver().resolve(
            rows=tuple(
                row(period)
                for period in range(1, 37)
            ),
            assessment_type="MIDTERM",
            semester=1,
        )


def test_ambiguous_target_marker_fails_closed():
    values = list(
        rows_with_marker(
            marker_period=37,
            marker_title="Kiem tra giua hoc ky I",
        )
    )
    values.append(
        row(
            38,
            "Kiem tra giua hoc ki 1",
        )
    )

    with pytest.raises(
        AssessmentPpctScopeResolutionError,
        match="ambiguous",
    ):
        AssessmentPpctScopeResolver().resolve(
            rows=tuple(values),
            assessment_type="MIDTERM",
            semester=1,
        )


def test_semester2_without_semester1_final_marker_fails_closed():
    values = tuple(
        [
            row(period)
            for period in range(73, 104)
        ]
        + [
            row(
                104,
                "Kiem tra giua hoc ky II",
            )
        ]
    )

    with pytest.raises(
        AssessmentPpctScopeResolutionError,
        match="FINAL semester 1 marker is missing",
    ):
        AssessmentPpctScopeResolver().resolve(
            rows=values,
            assessment_type="MIDTERM",
            semester=2,
        )


def test_mixed_subject_grade_scope_fails_closed():
    values = (
        row(1, subject_grade="Toan 8"),
        row(2, subject_grade="Toan 7"),
        row(
            3,
            "Kiem tra giua hoc ky I",
            subject_grade="Toan 8",
        ),
    )

    with pytest.raises(
        AssessmentPpctScopeResolutionError,
        match="more than one PPCT subject-grade scope",
    ):
        AssessmentPpctScopeResolver().resolve(
            rows=values,
            assessment_type="MIDTERM",
            semester=1,
        )


def test_mixed_sub_subject_scope_fails_closed():
    values = (
        row(
            1,
            sub_subject="Dai so",
        ),
        row(
            2,
            sub_subject="Hinh hoc",
        ),
        row(
            3,
            "Kiem tra giua hoc ky I",
            sub_subject="Dai so",
        ),
    )

    with pytest.raises(
        AssessmentPpctScopeResolutionError,
        match="more than one PPCT sub-subject scope",
    ):
        AssessmentPpctScopeResolver().resolve(
            rows=values,
            assessment_type="MIDTERM",
            semester=1,
        )


def test_empty_scope_fails_closed():
    with pytest.raises(
        AssessmentPpctScopeResolutionError,
        match="must not be empty",
    ):
        AssessmentPpctScopeResolver().resolve(
            rows=(),
            assessment_type="MIDTERM",
            semester=1,
        )


def test_marker_without_semester_is_not_guessed():
    values = (
        row(1),
        row(
            2,
            "Kiem tra giua hoc ky",
        ),
    )

    with pytest.raises(
        AssessmentPpctScopeResolutionError,
        match="marker not found",
    ):
        AssessmentPpctScopeResolver().resolve(
            rows=values,
            assessment_type="MIDTERM",
            semester=1,
        )