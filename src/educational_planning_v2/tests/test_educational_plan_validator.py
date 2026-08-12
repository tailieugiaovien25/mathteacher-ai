from educational_planning_v2.models import (
    CurriculumScope,
    EducationalPlan,
    EducationalPlanItem,
)
from educational_planning_v2.validators import EducationalPlanValidator


def make_valid_plan() -> EducationalPlan:
    from curriculum_v2.canonical_curriculum import get_canonical_curriculum

    curriculum = get_canonical_curriculum()
    requirement = curriculum.requirement_by_id("YCCD-MATH-06-0001")

    scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=6,
        curriculum_node_ids=(requirement.curriculum_node_ref,),
        canonical_requirement_ids=("YCCD-MATH-06-0001",),
    )
    item = EducationalPlanItem(
        plan_item_id="ITEM-001",
        title="Bài học",
        curriculum_scope=scope,
        periods=1,
        sequence=1,
    )
    return EducationalPlan(
        educational_plan_id="PLAN-001",
        academic_year="2026-2027",
        subject="MATHEMATICS",
        grade=6,
        items=(item,),
    )


def test_validator_accepts_valid_plan():
    result = EducationalPlanValidator().validate(make_valid_plan())

    assert result.is_valid is True
    assert result.violations == ()


def test_validator_rejects_invalid_canonical_node():
    plan = make_valid_plan()
    item = EducationalPlanItem(
        plan_item_id="ITEM-001",
        title="Bài học",
        curriculum_scope=CurriculumScope(
            curriculum_ref="CTGDPT-2018-MATH",
            grade=6,
            curriculum_node_ids=("CURR-NODE-MATH-G6-999",),
        ),
        periods=1,
        sequence=1,
    )
    invalid_plan = EducationalPlan(
        educational_plan_id=plan.educational_plan_id,
        academic_year=plan.academic_year,
        subject=plan.subject,
        grade=plan.grade,
        items=(item,),
    )

    result = EducationalPlanValidator().validate(invalid_plan)

    assert result.is_valid is False
    assert any(
        v.code == "PLAN_ITEM_CURRICULUM_INVALID"
        for v in result.violations
    )


def test_validator_combines_structure_and_curriculum_violations():
    item = EducationalPlanItem(
        plan_item_id="ITEM-001",
        title="Bài học",
        curriculum_scope=CurriculumScope(
            curriculum_ref="CTGDPT-2018-MATH",
            grade=7,
            curriculum_node_ids=("CURR-NODE-MATH-G7-999",),
        ),
        periods=0,
        sequence=1,
    )
    plan = EducationalPlan(
        educational_plan_id="PLAN-001",
        academic_year="2026-2027",
        subject="MATHEMATICS",
        grade=6,
        items=(item,),
    )

    result = EducationalPlanValidator().validate(plan)
    codes = {v.code for v in result.violations}

    assert result.is_valid is False
    assert "PLAN_ITEM_PERIODS_INVALID" in codes
    assert "PLAN_ITEM_GRADE_MISMATCH" in codes
    assert "PLAN_ITEM_CURRICULUM_INVALID" in codes


def test_validation_result_is_stable_tuple_contract():
    result = EducationalPlanValidator().validate(make_valid_plan())

    assert isinstance(result.violations, tuple)
