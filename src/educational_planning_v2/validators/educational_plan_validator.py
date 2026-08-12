from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.models import EducationalPlan
from educational_planning_v2.rules import (
    PlanningRuleViolation,
    validate_plan_structure,
)
from educational_planning_v2.services import PlanningContextService


@dataclass(frozen=True)
class EducationalPlanValidationResult:
    is_valid: bool
    violations: tuple[PlanningRuleViolation, ...]


class EducationalPlanValidator:
    """Validate plan structure and canonical curriculum references."""

    def __init__(
        self,
        context_service: PlanningContextService | None = None,
    ) -> None:
        self._context_service = context_service or PlanningContextService()

    def validate(
        self,
        plan: EducationalPlan,
    ) -> EducationalPlanValidationResult:
        violations = list(validate_plan_structure(plan))

        for item in plan.items:
            try:
                self._context_service.build(item.curriculum_scope)
            except (ValueError, LookupError) as exc:
                violations.append(
                    PlanningRuleViolation(
                        code="PLAN_ITEM_CURRICULUM_INVALID",
                        message=str(exc),
                        plan_item_id=item.plan_item_id,
                    )
                )

        return EducationalPlanValidationResult(
            is_valid=not violations,
            violations=tuple(violations),
        )
