import pytest

from curriculum_v2.canonical_curriculum import get_canonical_curriculum
from educational_planning_v2 import (
    CurriculumScope,
    EducationalPlanningFacade,
    get_educational_planning,
)
from educational_planning_v2.builders import PlanItemDraft


def canonical_draft(canonical_id: str) -> PlanItemDraft:
    curriculum = get_canonical_curriculum()
    requirement = curriculum.requirement_by_id(canonical_id)
    assert requirement is not None

    return PlanItemDraft(
        title="Bài học",
        periods=1,
        curriculum_node_ids=(requirement.curriculum_node_ref,),
        canonical_requirement_ids=(canonical_id,),
    )


def test_facade_builds_valid_plan():
    facade = EducationalPlanningFacade()

    plan = facade.build_plan(
        educational_plan_id="EDU-PLAN-MATH-G6-001",
        academic_year="2026-2027",
        subject="MATHEMATICS",
        grade=6,
        curriculum_ref="CTGDPT-2018-MATH",
        item_drafts=(canonical_draft("YCCD-MATH-06-0001"),),
    )

    assert plan.grade == 6
    assert len(plan.items) == 1


def test_facade_validates_plan():
    facade = EducationalPlanningFacade()
    plan = facade.build_plan(
        educational_plan_id="EDU-PLAN-MATH-G7-001",
        academic_year="2026-2027",
        subject="MATHEMATICS",
        grade=7,
        curriculum_ref="CTGDPT-2018-MATH",
        item_drafts=(canonical_draft("YCCD-MATH-07-0001"),),
    )

    result = facade.validate_plan(plan)

    assert result.is_valid is True
    assert result.violations == ()


def test_facade_resolves_scope():
    curriculum = get_canonical_curriculum()
    requirement = curriculum.requirement_by_id("YCCD-MATH-08-0001")
    assert requirement is not None

    scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=8,
        curriculum_node_ids=(requirement.curriculum_node_ref,),
        canonical_requirement_ids=("YCCD-MATH-08-0001",),
    )

    context = EducationalPlanningFacade().resolve_scope(scope)

    assert context.scope == scope
    assert context.requirements[0].canonical_id == "YCCD-MATH-08-0001"


def test_facade_rejects_invalid_build():
    facade = EducationalPlanningFacade()
    bad_draft = PlanItemDraft(
        title="Bài lỗi",
        periods=0,
    )

    with pytest.raises(ValueError, match="PLAN_ITEM_PERIODS_INVALID"):
        facade.build_plan(
            educational_plan_id="EDU-PLAN-MATH-G6-002",
            academic_year="2026-2027",
            subject="MATHEMATICS",
            grade=6,
            curriculum_ref="CTGDPT-2018-MATH",
            item_drafts=(bad_draft,),
        )


def test_facade_rejects_invalid_scope():
    scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=9,
        canonical_requirement_ids=("YCCD-MATH-09-9999",),
    )

    with pytest.raises(LookupError):
        EducationalPlanningFacade().resolve_scope(scope)


def test_default_facade_is_shared():
    first = get_educational_planning()
    second = get_educational_planning()

    assert first is second


def test_public_package_exports_facade():
    from educational_planning_v2 import EducationalPlanningFacade as Exported

    assert Exported is EducationalPlanningFacade
