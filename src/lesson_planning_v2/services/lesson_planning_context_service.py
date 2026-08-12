from educational_planning_v2.models import (
    EducationalPlan,
    EducationalPlanItem,
)
from educational_planning_v2.services.planning_context_service import (
    PlanningContextService,
)
from lesson_planning_v2.contexts import LessonPlanningContext


class LessonPlanningContextService:
    """Build trusted lesson-planning context from an educational plan item."""

    def __init__(
        self,
        planning_context_service: PlanningContextService | None = None,
    ) -> None:
        self._planning_context_service = (
            planning_context_service or PlanningContextService()
        )

    def build(
        self,
        plan: EducationalPlan,
        item: EducationalPlanItem,
    ) -> LessonPlanningContext:
        if item not in plan.items:
            raise ValueError(
                "educational plan item must belong to the educational plan"
            )

        if item.curriculum_scope.grade != plan.grade:
            raise ValueError(
                "plan item curriculum scope grade must match plan grade"
            )

        planning_context = self._planning_context_service.build(
            item.curriculum_scope
        )

        return LessonPlanningContext(
            educational_plan_id=plan.educational_plan_id,
            plan_item_id=item.plan_item_id,
            title=item.title,
            academic_year=plan.academic_year,
            subject=plan.subject,
            grade=plan.grade,
            periods=item.periods,
            curriculum_scope=planning_context.scope,
            nodes=planning_context.nodes,
            requirements=planning_context.requirements,
        )


def get_lesson_planning_context_service() -> LessonPlanningContextService:
    return LessonPlanningContextService()
