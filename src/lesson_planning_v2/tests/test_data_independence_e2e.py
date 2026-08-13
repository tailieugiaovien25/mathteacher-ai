import pytest

from educational_planning_v2.builders import (
    EducationalPlanBuilder,
    PlanItemDraft,
)
from lesson_planning_v2.builders import LessonPlanBuilder, LessonPlanDraft
from lesson_planning_v2.models import LessonObjective, PeriodPlan
from lesson_planning_v2.services import LessonPlanningContextService


@pytest.mark.parametrize(
    ("case_id", "title", "node_id", "requirement_id"),
    (
        (
            "natural-number-set",
            "Tập hợp số tự nhiên",
            "CURR-NODE-MATH-G6-004",
            "YCCD-MATH-06-0001",
        ),
        (
            "natural-number-operations",
            "Phép tính với số tự nhiên",
            "CURR-NODE-MATH-G6-005",
            "YCCD-MATH-06-0006",
        ),
    ),
)
def test_data_changes_without_changing_the_planning_pipeline(
    case_id,
    title,
    node_id,
    requirement_id,
):
    educational_plan = EducationalPlanBuilder().build(
        educational_plan_id=f"EP-E2E-{case_id}",
        academic_year="2026-2027",
        subject="Mathematics",
        grade=6,
        curriculum_ref="CURRICULUM-MATH-2018",
        item_drafts=(
            PlanItemDraft(
                title=title,
                periods=1,
                curriculum_node_ids=(node_id,),
                canonical_requirement_ids=(requirement_id,),
            ),
        ),
    )
    plan_item = educational_plan.items[0]

    context = LessonPlanningContextService().build(
        educational_plan,
        plan_item,
    )
    lesson_plan = LessonPlanBuilder().build(
        lesson_plan_id=f"LP-E2E-{case_id}",
        context=context,
        draft=LessonPlanDraft(
            objectives=(
                LessonObjective(
                    objective_id=f"OBJ-E2E-{case_id}",
                    objective_type="KNOWLEDGE",
                    statement=context.requirements[0].requirement_text_original,
                    source_requirement_refs=(requirement_id,),
                ),
            ),
            periods=(PeriodPlan(1),),
        ),
    )

    assert lesson_plan.curriculum_node_refs == (node_id,)
    assert lesson_plan.canonical_requirement_refs == (requirement_id,)
    assert lesson_plan.objectives[0].statement == (
        context.requirements[0].requirement_text_original
    )
