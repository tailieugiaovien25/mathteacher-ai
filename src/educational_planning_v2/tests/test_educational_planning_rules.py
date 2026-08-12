from educational_planning_v2.models import (
    CurriculumScope,
    EducationalPlan,
    EducationalPlanItem,
)
from educational_planning_v2.rules import validate_plan_structure


def make_item(
    item_id: str = "ITEM-001",
    *,
    grade: int = 6,
    periods: int = 1,
    sequence: int = 1,
) -> EducationalPlanItem:
    return EducationalPlanItem(
        plan_item_id=item_id,
        title="Bài học",
        curriculum_scope=CurriculumScope(
            curriculum_ref="CTGDPT-2018-MATH",
            grade=grade,
        ),
        periods=periods,
        sequence=sequence,
    )


def make_plan(*items: EducationalPlanItem, grade: int = 6) -> EducationalPlan:
    return EducationalPlan(
        educational_plan_id="PLAN-001",
        academic_year="2026-2027",
        subject="MATHEMATICS",
        grade=grade,
        items=items,
    )


def codes(plan: EducationalPlan) -> set[str]:
    return {v.code for v in validate_plan_structure(plan)}


def test_valid_structure_has_no_violations():
    assert validate_plan_structure(make_plan(make_item())) == ()


def test_invalid_plan_grade_is_reported():
    assert "PLAN_GRADE_INVALID" in codes(make_plan(grade=10))


def test_duplicate_item_id_is_reported():
    plan = make_plan(
        make_item("ITEM-001", sequence=1),
        make_item("ITEM-001", sequence=2),
    )
    assert "PLAN_ITEM_ID_DUPLICATE" in codes(plan)


def test_non_positive_periods_are_reported():
    assert "PLAN_ITEM_PERIODS_INVALID" in codes(
        make_plan(make_item(periods=0))
    )


def test_negative_sequence_is_reported():
    assert "PLAN_ITEM_SEQUENCE_INVALID" in codes(
        make_plan(make_item(sequence=-1))
    )


def test_duplicate_sequence_is_reported():
    plan = make_plan(
        make_item("ITEM-001", sequence=1),
        make_item("ITEM-002", sequence=1),
    )
    assert "PLAN_ITEM_SEQUENCE_DUPLICATE" in codes(plan)


def test_scope_grade_mismatch_is_reported():
    plan = make_plan(make_item(grade=7), grade=6)
    assert "PLAN_ITEM_GRADE_MISMATCH" in codes(plan)
