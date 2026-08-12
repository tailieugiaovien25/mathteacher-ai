from dataclasses import FrozenInstanceError

import pytest

from educational_planning_v2.models import (
    CurriculumScope,
    EducationalPlan,
    EducationalPlanItem,
)


def make_scope() -> CurriculumScope:
    return CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=6,
        curriculum_node_ids=("CURR-NODE-MATH-G6-001",),
        canonical_requirement_ids=("YCCD-MATH-06-0001",),
    )


def test_curriculum_scope_keeps_canonical_references():
    scope = make_scope()

    assert scope.grade == 6
    assert scope.curriculum_node_ids == ("CURR-NODE-MATH-G6-001",)
    assert scope.canonical_requirement_ids == ("YCCD-MATH-06-0001",)


def test_curriculum_scope_defaults_are_safe():
    scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=7,
    )

    assert scope.curriculum_node_ids == ()
    assert scope.canonical_requirement_ids == ()
    assert scope.metadata == {}


def test_plan_item_contains_curriculum_scope():
    item = EducationalPlanItem(
        plan_item_id="PLAN-ITEM-001",
        title="Bài học thử nghiệm",
        curriculum_scope=make_scope(),
        periods=2,
        sequence=1,
    )

    assert item.curriculum_scope.grade == 6
    assert item.periods == 2
    assert item.sequence == 1


def test_plan_item_supports_planning_fields():
    item = EducationalPlanItem(
        plan_item_id="PLAN-ITEM-001",
        title="Bài học thử nghiệm",
        curriculum_scope=make_scope(),
        periods=1,
        planned_time="Tuần 1",
        teaching_equipment=("Máy chiếu",),
        teaching_location="Phòng học",
    )

    assert item.planned_time == "Tuần 1"
    assert item.teaching_equipment == ("Máy chiếu",)
    assert item.teaching_location == "Phòng học"


def test_educational_plan_contains_items():
    item = EducationalPlanItem(
        plan_item_id="PLAN-ITEM-001",
        title="Bài học thử nghiệm",
        curriculum_scope=make_scope(),
        periods=2,
    )
    plan = EducationalPlan(
        educational_plan_id="EDU-PLAN-MATH-G6-001",
        academic_year="2026-2027",
        subject="MATHEMATICS",
        grade=6,
        items=(item,),
    )

    assert len(plan.items) == 1
    assert plan.items[0].plan_item_id == "PLAN-ITEM-001"


def test_contracts_are_frozen():
    scope = make_scope()

    with pytest.raises(FrozenInstanceError):
        scope.grade = 9


def test_plan_defaults_to_draft():
    plan = EducationalPlan(
        educational_plan_id="EDU-PLAN-MATH-G8-001",
        academic_year="2026-2027",
        subject="MATHEMATICS",
        grade=8,
    )

    assert plan.status == "DRAFT"
    assert plan.items == ()
    assert plan.metadata == {}
