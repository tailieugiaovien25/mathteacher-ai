import pytest

from curriculum_v2.canonical_curriculum import get_canonical_curriculum
from educational_planning_v2.builders import (
    EducationalPlanBuilder,
    PlanItemDraft,
)


def canonical_draft(
    canonical_id: str,
    *,
    title: str = "Bài học",
    periods: int = 1,
) -> PlanItemDraft:
    curriculum = get_canonical_curriculum()
    requirement = curriculum.requirement_by_id(canonical_id)
    assert requirement is not None

    return PlanItemDraft(
        title=title,
        periods=periods,
        curriculum_node_ids=(requirement.curriculum_node_ref,),
        canonical_requirement_ids=(canonical_id,),
    )


def build_grade6(*drafts: PlanItemDraft):
    return EducationalPlanBuilder().build(
        educational_plan_id="EDU-PLAN-MATH-G6-001",
        academic_year="2026-2027",
        subject="MATHEMATICS",
        grade=6,
        curriculum_ref="CTGDPT-2018-MATH",
        item_drafts=tuple(drafts),
    )


def test_builder_creates_valid_plan():
    plan = build_grade6(canonical_draft("YCCD-MATH-06-0001"))

    assert plan.educational_plan_id == "EDU-PLAN-MATH-G6-001"
    assert plan.grade == 6
    assert len(plan.items) == 1


def test_builder_assigns_stable_item_ids_and_sequences():
    plan = build_grade6(
        canonical_draft("YCCD-MATH-06-0001", title="Bài 1"),
        canonical_draft("YCCD-MATH-06-0002", title="Bài 2"),
    )

    assert [item.plan_item_id for item in plan.items] == [
        "EDU-PLAN-MATH-G6-001-ITEM-001",
        "EDU-PLAN-MATH-G6-001-ITEM-002",
    ]
    assert [item.sequence for item in plan.items] == [1, 2]


def test_builder_preserves_canonical_references():
    plan = build_grade6(canonical_draft("YCCD-MATH-06-0001"))
    item = plan.items[0]

    assert item.curriculum_scope.canonical_requirement_ids == (
        "YCCD-MATH-06-0001",
    )
    assert item.curriculum_scope.curriculum_node_ids


def test_builder_preserves_planning_fields():
    draft = canonical_draft("YCCD-MATH-06-0001")
    draft = PlanItemDraft(
        title=draft.title,
        periods=2,
        curriculum_node_ids=draft.curriculum_node_ids,
        canonical_requirement_ids=draft.canonical_requirement_ids,
        planned_time="Tuần 1",
        teaching_equipment=("Máy chiếu",),
        teaching_location="Phòng học",
    )

    plan = build_grade6(draft)
    item = plan.items[0]

    assert item.periods == 2
    assert item.planned_time == "Tuần 1"
    assert item.teaching_equipment == ("Máy chiếu",)
    assert item.teaching_location == "Phòng học"


def test_builder_rejects_non_positive_periods():
    with pytest.raises(ValueError, match="PLAN_ITEM_PERIODS_INVALID"):
        build_grade6(
            canonical_draft(
                "YCCD-MATH-06-0001",
                periods=0,
            )
        )


def test_builder_rejects_missing_canonical_requirement():
    draft = PlanItemDraft(
        title="Bài lỗi",
        periods=1,
        curriculum_node_ids=("CURR-NODE-MATH-G6-001",),
        canonical_requirement_ids=("YCCD-MATH-06-9999",),
    )

    with pytest.raises(ValueError, match="PLAN_ITEM_CURRICULUM_INVALID"):
        build_grade6(draft)


def test_builder_rejects_wrong_grade_reference():
    draft = canonical_draft("YCCD-MATH-07-0001")

    with pytest.raises(ValueError, match="PLAN_ITEM_CURRICULUM_INVALID"):
        build_grade6(draft)


def test_builder_allows_empty_plan():
    plan = build_grade6()

    assert plan.items == ()
    assert plan.status == "DRAFT"


def test_builder_supports_explicit_status():
    builder = EducationalPlanBuilder()
    plan = builder.build(
        educational_plan_id="EDU-PLAN-MATH-G6-002",
        academic_year="2026-2027",
        subject="MATHEMATICS",
        grade=6,
        curriculum_ref="CTGDPT-2018-MATH",
        item_drafts=(),
        status="CANDIDATE",
    )

    assert plan.status == "CANDIDATE"
