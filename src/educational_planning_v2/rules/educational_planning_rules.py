from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.models import EducationalPlan


@dataclass(frozen=True)
class PlanningRuleViolation:
    code: str
    message: str
    plan_item_id: str | None = None


def validate_plan_structure(
    plan: EducationalPlan,
) -> tuple[PlanningRuleViolation, ...]:
    """Validate planning-domain structural rules without canonical I/O."""

    violations: list[PlanningRuleViolation] = []

    if plan.grade not in {6, 7, 8, 9}:
        violations.append(
            PlanningRuleViolation(
                code="PLAN_GRADE_INVALID",
                message="Plan grade must be one of 6, 7, 8, 9.",
            )
        )

    seen_ids: set[str] = set()
    seen_sequences: set[int] = set()

    for item in plan.items:
        if item.plan_item_id in seen_ids:
            violations.append(
                PlanningRuleViolation(
                    code="PLAN_ITEM_ID_DUPLICATE",
                    message="Plan item IDs must be unique.",
                    plan_item_id=item.plan_item_id,
                )
            )
        seen_ids.add(item.plan_item_id)

        if item.periods <= 0:
            violations.append(
                PlanningRuleViolation(
                    code="PLAN_ITEM_PERIODS_INVALID",
                    message="Plan item periods must be greater than zero.",
                    plan_item_id=item.plan_item_id,
                )
            )

        if item.sequence < 0:
            violations.append(
                PlanningRuleViolation(
                    code="PLAN_ITEM_SEQUENCE_INVALID",
                    message="Plan item sequence must not be negative.",
                    plan_item_id=item.plan_item_id,
                )
            )

        if item.sequence in seen_sequences:
            violations.append(
                PlanningRuleViolation(
                    code="PLAN_ITEM_SEQUENCE_DUPLICATE",
                    message="Plan item sequence values must be unique.",
                    plan_item_id=item.plan_item_id,
                )
            )
        seen_sequences.add(item.sequence)

        if item.curriculum_scope.grade != plan.grade:
            violations.append(
                PlanningRuleViolation(
                    code="PLAN_ITEM_GRADE_MISMATCH",
                    message=(
                        "Plan item curriculum scope grade must match plan grade."
                    ),
                    plan_item_id=item.plan_item_id,
                )
            )

    return tuple(violations)
