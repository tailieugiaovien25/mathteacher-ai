import pytest

from educational_planning_v2.adapters.ppct_curriculum_source_adapter import (
    PpctCurriculumSourceAdapter,
    PpctCurriculumSourceAdapterError,
    PpctSourceContext,
)
from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)


def _context(
    *,
    source_version="7",
):
    return PpctSourceContext(
        source_id="SRC-PPCT-MATH7-2026",
        source_version=source_version,
        academic_year="2026-2027",
        subject_code="MATH",
        grade_level=7,
        source_location="workbook:PPCT",
    )


def _row(
    period,
    lesson_name,
    *,
    sub_subject=None,
):
    return PPCTRow(
        subject_grade="Toán 7",
        period=period,
        lesson_name=lesson_name,
        sub_subject=sub_subject,
    )


def test_ppct_adapter_emits_generic_source_items_in_period_order():
    result = PpctCurriculumSourceAdapter().adapt(
        rows=(
            _row(2, "Bài 1. Tập hợp"),
            _row(1, "Mở đầu"),
        ),
        context=_context(),
    )

    assert tuple(
        item.sequence
        for item in result
    ) == (1, 2)

    assert tuple(
        item.external_item_key
        for item in result
    ) == (
        "PERIOD:0001",
        "PERIOD:0002",
    )

    assert all(
        item.source_type == "PPCT"
        for item in result
    )


def test_title_is_metadata_not_source_identity():
    adapter = PpctCurriculumSourceAdapter()

    first = adapter.adapt(
        rows=(
            _row(
                12,
                "Tên bài theo bản nguồn A",
            ),
        ),
        context=_context(),
    )[0]

    second = adapter.adapt(
        rows=(
            _row(
                12,
                "Tên hiển thị được sửa",
            ),
        ),
        context=_context(),
    )[0]

    assert first.identity == second.identity
    assert first.title != second.title


def test_source_version_change_changes_identity_without_code_change():
    adapter = PpctCurriculumSourceAdapter()

    version_7 = adapter.adapt(
        rows=(
            _row(12, "Bài 4"),
        ),
        context=_context(
            source_version="7",
        ),
    )[0]

    version_8 = adapter.adapt(
        rows=(
            _row(12, "Bài 4"),
        ),
        context=_context(
            source_version="8",
        ),
    )[0]

    assert (
        version_7.identity
        != version_8.identity
    )

    assert (
        version_7.external_item_key
        == version_8.external_item_key
    )


def test_exact_duplicate_period_rows_collapse():
    result = PpctCurriculumSourceAdapter().adapt(
        rows=(
            _row(34, "Kiểm tra giữa học kì I"),
            _row(34, "Kiểm tra giữa học kì I"),
        ),
        context=_context(),
    )

    assert len(result) == 1
    assert result[0].sequence == 34


def test_conflicting_rows_for_same_period_fail_closed():
    with pytest.raises(
        PpctCurriculumSourceAdapterError,
        match="ambiguous",
    ):
        PpctCurriculumSourceAdapter().adapt(
            rows=(
                _row(34, "Bài A"),
                _row(34, "Bài B"),
            ),
            context=_context(),
        )


def test_multi_period_same_lesson_remains_two_source_items():
    result = PpctCurriculumSourceAdapter().adapt(
        rows=(
            _row(25, "Bài 5"),
            _row(26, "Bài 5"),
        ),
        context=_context(),
    )

    assert tuple(
        item.external_item_key
        for item in result
    ) == (
        "PERIOD:0025",
        "PERIOD:0026",
    )

    assert result[0].title == result[1].title


def test_adapter_does_not_infer_canonical_lesson_id():
    item = PpctCurriculumSourceAdapter().adapt(
        rows=(
            _row(1, "Bài 1"),
        ),
        context=_context(),
    )[0]

    assert not hasattr(
        item,
        "canonical_lesson_id",
    )


def test_context_is_explicit_not_inferred_from_subject_grade():
    context = PpctSourceContext(
        source_id="SRC-X",
        source_version="1",
        academic_year="2026-2027",
        subject_code="MATH",
        grade_level=8,
    )

    item = PpctCurriculumSourceAdapter().adapt(
        rows=(
            PPCTRow(
                subject_grade=(
                    "Nhãn nguồn có thể thay đổi"
                ),
                period=1,
                lesson_name="Bài 1",
                sub_subject=None,
            ),
        ),
        context=context,
    )[0]

    assert item.grade_level == 8
    assert item.subject_code == "MATH"


def test_empty_source_version_is_rejected():
    with pytest.raises(
        PpctCurriculumSourceAdapterError,
        match="source_version",
    ):
        _context(
            source_version=" ",
        )
