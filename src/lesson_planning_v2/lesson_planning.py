from __future__ import annotations

from educational_planning_v2.models import (
    EducationalPlan,
    EducationalPlanItem,
)
from educational_planning_v2.services import PlanningContextService
from lesson_planning_v2.builders import (
    LessonPlanBuilder,
    LessonPlanDraft,
)
from lesson_planning_v2.contexts import LessonPlanningContext
from lesson_planning_v2.models import LessonPlan
from lesson_planning_v2.services import LessonPlanningContextService
from lesson_planning_v2.validators import LessonPlanValidator
from core_v2.validation.validation_result import ValidationResult


class LessonPlanningFacade:
    """Stable public API for the lesson-planning subsystem."""

    def __init__(
        self,
        *,
        context_service: LessonPlanningContextService | None = None,
        validator: LessonPlanValidator | None = None,
        builder: LessonPlanBuilder | None = None,
        planning_context_service: PlanningContextService | None = None,
    ) -> None:
        self._context_service = context_service or LessonPlanningContextService(
            planning_context_service=planning_context_service,
        )
        self._validator = validator or LessonPlanValidator()
        self._builder = builder or LessonPlanBuilder(
            validator=self._validator,
        )

    def build_context(
        self,
        plan: EducationalPlan,
        item: EducationalPlanItem,
    ) -> LessonPlanningContext:
        return self._context_service.build(plan, item)

    def build_plan(
        self,
        *,
        lesson_plan_id: str,
        context: LessonPlanningContext,
        draft: LessonPlanDraft,
    ) -> LessonPlan:
        return self._builder.build(
            lesson_plan_id=lesson_plan_id,
            context=context,
            draft=draft,
        )

    def validate_plan(
        self,
        plan: LessonPlan,
    ) -> ValidationResult:
        return self._validator.validate(plan)


_default_facade: LessonPlanningFacade | None = None


def get_lesson_planning() -> LessonPlanningFacade:
    """Return the shared public lesson-planning facade."""
    global _default_facade
    if _default_facade is None:
        _default_facade = LessonPlanningFacade()
    return _default_facade
