import pytest

from assessment_generation_v2.services.assessment_ppct_scope_resolver import (
    AssessmentPpctScopeResolutionError,
    AssessmentPpctScopeResolver,
)
from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)


def _row(
    period: int,
    lesson_name: str,
) -> PPCTRow:
    return PPCTRow(
        subject_grade="Toán 7",
        period=period,
        lesson_name=lesson_name,
        sub_subject=None,
    )


def test_same_title_consecutive_midterm_rows_form_one_span():
    rows = (
        _row(31, "Bài 7. Tập hợp các số thực"),
        _row(32, "Ôn tập giữa học kì I"),
        _row(33, "Ôn tập giữa học kì I"),
        _row(34, "Kiểm tra giữa học kì I"),
        _row(35, "Kiểm tra giữa học kì I"),
        _row(36, "Luyện tập chung"),
    )

    result = AssessmentPpctScopeResolver().resolve(
        rows=rows,
        assessment_type="MIDTERM",
        semester=1,
    )

    assert result.marker_period == 34
    assert result.marker_title == "Kiểm tra giữa học kì I"
    assert result.period_from == 31
    assert result.period_to == 33
    assert tuple(row.period for row in result.scope_rows) == (31, 32, 33)


def test_consecutive_marker_rows_with_different_folded_titles_remain_ambiguous():
    rows = (
        _row(36, "Bài trước kiểm tra"),
        _row(37, "Kiem tra giua hoc ky I"),
        _row(38, "Kiem tra giua hoc ki 1"),
        _row(39, "Bài sau kiểm tra"),
    )

    with pytest.raises(
        AssessmentPpctScopeResolutionError,
        match="ambiguous",
    ):
        AssessmentPpctScopeResolver().resolve(
            rows=rows,
            assessment_type="MIDTERM",
            semester=1,
        )


def test_same_title_non_contiguous_marker_groups_remain_ambiguous():
    rows = (
        _row(32, "Ôn tập giữa học kì I"),
        _row(33, "Kiểm tra giữa học kì I"),
        _row(34, "Luyện tập chung"),
        _row(35, "Kiểm tra giữa học kì I"),
    )

    with pytest.raises(
        AssessmentPpctScopeResolutionError,
        match="ambiguous",
    ):
        AssessmentPpctScopeResolver().resolve(
            rows=rows,
            assessment_type="MIDTERM",
            semester=1,
        )


def test_same_period_exact_duplicate_markers_collapse():
    rows = (
        _row(32, "Ôn tập giữa học kì I"),
        _row(33, "Ôn tập giữa học kì I"),
        _row(34, "Kiểm tra giữa học kì I"),
        _row(34, "Kiểm tra giữa học kì I"),
        _row(35, "Luyện tập chung"),
    )

    result = AssessmentPpctScopeResolver().resolve(
        rows=rows,
        assessment_type="MIDTERM",
        semester=1,
    )

    assert result.marker_period == 34
    assert result.period_to == 33


def test_semester2_starts_after_end_of_same_title_final_span():
    rows = (
        _row(50, "Ôn tập cuối học kì I"),
        _row(51, "Kiểm tra cuối học kì I"),
        _row(52, "Kiểm tra cuối học kì I"),
        _row(53, "Bài mở đầu học kì II"),
        _row(54, "Bài tiếp theo học kì II"),
        _row(79, "Ôn tập giữa học kì II"),
        _row(80, "Kiểm tra giữa học kì II"),
        _row(81, "Kiểm tra giữa học kì II"),
        _row(82, "Luyện tập chung"),
    )

    result = AssessmentPpctScopeResolver().resolve(
        rows=rows,
        assessment_type="MIDTERM",
        semester=2,
    )

    assert result.marker_period == 80
    assert result.period_from == 53
    assert result.period_to == 79
    assert 51 not in tuple(row.period for row in result.scope_rows)
    assert 52 not in tuple(row.period for row in result.scope_rows)
