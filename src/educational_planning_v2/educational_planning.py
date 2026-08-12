from __future__ import annotations

from educational_planning_v2.builders import (
    EducationalPlanBuilder,
    PlanItemDraft,
)
from educational_planning_v2.models import (
    CurriculumScope,
    EducationalPlan,
)
from educational_planning_v2.services import (
    PlanningContext,
    PlanningContextService,
)
from educational_planning_v2.validators import (
    EducationalPlanValidationResult,
    EducationalPlanValidator,
)


class EducationalPlanningFacade:
    """Stable public API for the educational planning subsystem."""

    def __init__(
        self,
        *,
        builder: EducationalPlanBuilder | None = None,
        validator: EducationalPlanValidator | None = None,
        context_service: PlanningContextService | None = None,
    ) -> None:
        self._context_service = context_service or PlanningContextService()
        self._validator = validator or EducationalPlanValidator(
            context_service=self._context_service,
        )
        self._builder = builder or EducationalPlanBuilder(
            validator=self._validator,
        )

    def build_plan(
        self,
        *,
        educational_plan_id: str,
        academic_year: str,
        subject: str,
        grade: int,
        curriculum_ref: str,
        item_drafts: tuple[PlanItemDraft, ...],
        status: str = "DRAFT",
    ) -> EducationalPlan:
        return self._builder.build(
            educational_plan_id=educational_plan_id,
            academic_year=academic_year,
            subject=subject,
            grade=grade,
            curriculum_ref=curriculum_ref,
            item_drafts=item_drafts,
            status=status,
        )

    def validate_plan(
        self,
        plan: EducationalPlan,
    ) -> EducationalPlanValidationResult:
        return self._validator.validate(plan)

    def resolve_scope(
        self,
        scope: CurriculumScope,
    ) -> PlanningContext:
        return self._context_service.build(scope)


_default_facade: EducationalPlanningFacade | None = None


def get_educational_planning() -> EducationalPlanningFacade:
    """Return the shared public educational-planning facade."""
    global _default_facade
    if _default_facade is None:
        _default_facade = EducationalPlanningFacade()
    return _default_facade
