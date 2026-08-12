import pytest

from curriculum_v2.models.canonical_learning_requirement import (
    CanonicalLearningRequirement,
    RequirementProvenance,
    RequirementValidation,
)
from curriculum_v2.models.curriculum_node import CurriculumNode
from educational_planning_v2.models import CurriculumScope
from lesson_planning_v2.builders import (
    LessonPlanBuilder,
    LessonPlanDraft,
)
from lesson_planning_v2.contexts import LessonPlanningContext
from lesson_planning_v2.models import (
    LearningActivity,
    LessonObjective,
    PeriodPlan,
    TeachingResource,
)


def make_requirement():
    return CanonicalLearningRequirement(
        canonical_id="YCCD-MATH-06-0001",
        curriculum_ref="CTGDPT-2018-MATH",
        curriculum_node_ref="CURR-NODE-MATH-G6-001",
        requirement_text_original="Yêu cầu cần đạt thử nghiệm.",
        provenance=RequirementProvenance(
            legal_authority="MOET",
            regulation_id="TEST-REGULATION",
            source_document_id="TEST-DOCUMENT",
        ),
        validation=RequirementValidation(
            text_integrity="VERIFIED",
            structural_integrity="VERIFIED",
            provenance_integrity="VERIFIED",
            identity_integrity="VERIFIED",
        ),
        status="ACTIVE",
    )


def make_context(periods=2):
    scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=6,
        curriculum_node_ids=("CURR-NODE-MATH-G6-001",),
        canonical_requirement_ids=("YCCD-MATH-06-0001",),
    )
    node = CurriculumNode(
        curriculum_node_id="CURR-NODE-MATH-G6-001",
        curriculum_ref="CTGDPT-2018-MATH",
        code="MATH6-001",
        name="Nút chương trình",
        node_type="LESSON",
    )
    return LessonPlanningContext(
        educational_plan_id="EP-001",
        plan_item_id="ITEM-001",
        title="Bài học thử nghiệm",
        academic_year="2026-2027",
        subject="Mathematics",
        grade=6,
        periods=periods,
        curriculum_scope=scope,
        nodes=(node,),
        requirements=(make_requirement(),),
    )


def make_valid_draft():
    objective = LessonObjective(
        objective_id="OBJ-001",
        objective_type="KNOWLEDGE",
        statement="Mục tiêu",
        source_requirement_refs=("YCCD-MATH-06-0001",),
    )
    resource = TeachingResource(
        resource_id="RES-001",
        name="Phiếu học tập",
        resource_type="WORKSHEET",
    )
    activity = LearningActivity(
        activity_id="ACT-001",
        title="Khám phá",
        activity_type="LEARNING",
        order=1,
        objective_refs=("OBJ-001",),
        resource_refs=("RES-001",),
    )
    return LessonPlanDraft(
        objectives=(objective,),
        resources=(resource,),
        periods=(PeriodPlan(1, (activity,)),),
    )


def test_builder_uses_context_identity():
    plan = LessonPlanBuilder().build(
        lesson_plan_id="LP-001",
        context=make_context(),
        draft=make_valid_draft(),
    )

    assert plan.educational_plan_id == "EP-001"
    assert plan.plan_item_id == "ITEM-001"
    assert plan.title == "Bài học thử nghiệm"
    assert plan.grade == 6


def test_builder_uses_context_period_count():
    plan = LessonPlanBuilder().build(
        lesson_plan_id="LP-001",
        context=make_context(periods=3),
        draft=make_valid_draft(),
    )

    assert plan.total_periods == 3


def test_builder_preserves_canonical_context_refs():
    plan = LessonPlanBuilder().build(
        lesson_plan_id="LP-001",
        context=make_context(),
        draft=make_valid_draft(),
    )

    assert plan.curriculum_node_refs == (
        "CURR-NODE-MATH-G6-001",
    )
    assert plan.canonical_requirement_refs == (
        "YCCD-MATH-06-0001",
    )


def test_builder_preserves_draft_semantic_content():
    draft = make_valid_draft()
    plan = LessonPlanBuilder().build(
        lesson_plan_id="LP-001",
        context=make_context(),
        draft=draft,
    )

    assert plan.objectives == draft.objectives
    assert plan.resources == draft.resources
    assert plan.periods == draft.periods


def test_builder_supports_single_period_mode():
    draft = LessonPlanDraft(
        plan_mode="SINGLE_PERIOD",
        period_in_lesson=2,
        periods=(PeriodPlan(2),),
    )

    plan = LessonPlanBuilder().build(
        lesson_plan_id="LP-002",
        context=make_context(periods=3),
        draft=draft,
    )

    assert plan.plan_mode == "SINGLE_PERIOD"
    assert plan.period_in_lesson == 2
    assert plan.total_periods == 3


def test_builder_rejects_invalid_single_period():
    draft = LessonPlanDraft(
        plan_mode="SINGLE_PERIOD",
        period_in_lesson=3,
        periods=(PeriodPlan(3),),
    )

    with pytest.raises(
        ValueError,
        match="LESSON_PLAN_PERIOD_INVALID",
    ):
        LessonPlanBuilder().build(
            lesson_plan_id="LP-003",
            context=make_context(periods=2),
            draft=draft,
        )


def test_builder_rejects_requirement_outside_context():
    objective = LessonObjective(
        objective_id="OBJ-X",
        objective_type="KNOWLEDGE",
        statement="Mục tiêu ngoài scope",
        source_requirement_refs=("YCCD-OUTSIDE",),
    )
    draft = LessonPlanDraft(
        objectives=(objective,),
        periods=(PeriodPlan(1),),
    )

    with pytest.raises(
        ValueError,
        match="LESSON_OBJECTIVE_REQUIREMENT_REF_INVALID",
    ):
        LessonPlanBuilder().build(
            lesson_plan_id="LP-004",
            context=make_context(),
            draft=draft,
        )


def test_builder_rejects_dangling_activity_reference():
    activity = LearningActivity(
        activity_id="ACT-X",
        title="Sai tham chiếu",
        activity_type="LEARNING",
        order=1,
        objective_refs=("OBJ-NOT-FOUND",),
    )
    draft = LessonPlanDraft(
        periods=(PeriodPlan(1, (activity,)),),
    )

    with pytest.raises(
        ValueError,
        match="LESSON_ACTIVITY_OBJECTIVE_REF_INVALID",
    ):
        LessonPlanBuilder().build(
            lesson_plan_id="LP-005",
            context=make_context(),
            draft=draft,
        )


def test_builder_does_not_query_curriculum_directly():
    context = make_context()
    plan = LessonPlanBuilder().build(
        lesson_plan_id="LP-006",
        context=context,
        draft=make_valid_draft(),
    )

    assert plan.canonical_requirement_refs == tuple(
        requirement.canonical_id
        for requirement in context.requirements
    )


def test_builder_uses_core_validation_issues_for_error_details():
    draft = LessonPlanDraft(
        plan_mode="UNKNOWN",
        periods=(PeriodPlan(1),),
    )

    with pytest.raises(
        ValueError,
        match="LESSON_PLAN_MODE_INVALID",
    ):
        LessonPlanBuilder().build(
            lesson_plan_id="LP-007",
            context=make_context(),
            draft=draft,
        )
