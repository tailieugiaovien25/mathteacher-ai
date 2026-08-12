from dataclasses import dataclass

from lesson_planning_v2.models import LessonPlan


@dataclass(frozen=True)
class LessonPlanningRuleViolation:
    code: str
    message: str
    field: str | None = None


def validate_lesson_plan_structure(
    plan: LessonPlan,
) -> tuple[LessonPlanningRuleViolation, ...]:
    """Validate lesson-planning domain rules without external I/O."""
    violations: list[LessonPlanningRuleViolation] = []

    if plan.plan_mode not in {"FULL_LESSON", "SINGLE_PERIOD"}:
        violations.append(
            LessonPlanningRuleViolation(
                code="LESSON_PLAN_MODE_INVALID",
                message="Plan mode must be FULL_LESSON or SINGLE_PERIOD.",
                field="plan_mode",
            )
        )

    if plan.total_periods <= 0:
        violations.append(
            LessonPlanningRuleViolation(
                code="LESSON_PLAN_TOTAL_PERIODS_INVALID",
                message="Total periods must be greater than zero.",
                field="total_periods",
            )
        )

    if plan.plan_mode == "FULL_LESSON" and plan.period_in_lesson is not None:
        violations.append(
            LessonPlanningRuleViolation(
                code="LESSON_PLAN_PERIOD_INVALID",
                message="FULL_LESSON must not select one period.",
                field="period_in_lesson",
            )
        )

    if plan.plan_mode == "SINGLE_PERIOD":
        if (
            plan.period_in_lesson is None
            or plan.period_in_lesson <= 0
            or plan.period_in_lesson > plan.total_periods
        ):
            violations.append(
                LessonPlanningRuleViolation(
                    code="LESSON_PLAN_PERIOD_INVALID",
                    message=(
                        "SINGLE_PERIOD must select a period from 1 "
                        "through total_periods."
                    ),
                    field="period_in_lesson",
                )
            )

    objective_ids: set[str] = set()
    for objective in plan.objectives:
        if objective.objective_id in objective_ids:
            violations.append(
                LessonPlanningRuleViolation(
                    code="LESSON_OBJECTIVE_ID_DUPLICATE",
                    message="Objective IDs must be unique.",
                    field="objectives",
                )
            )
        objective_ids.add(objective.objective_id)

        for requirement_ref in objective.source_requirement_refs:
            if requirement_ref not in plan.canonical_requirement_refs:
                violations.append(
                    LessonPlanningRuleViolation(
                        code="LESSON_OBJECTIVE_REQUIREMENT_REF_INVALID",
                        message=(
                            "Objective requirement references must belong "
                            "to the lesson plan canonical requirement scope."
                        ),
                        field="objectives",
                    )
                )

    resource_ids: set[str] = set()
    for resource in plan.resources:
        if resource.resource_id in resource_ids:
            violations.append(
                LessonPlanningRuleViolation(
                    code="LESSON_RESOURCE_ID_DUPLICATE",
                    message="Resource IDs must be unique.",
                    field="resources",
                )
            )
        resource_ids.add(resource.resource_id)

    period_numbers: set[int] = set()
    activity_ids: set[str] = set()

    for period in plan.periods:
        if (
            period.period_in_lesson <= 0
            or period.period_in_lesson > plan.total_periods
        ):
            violations.append(
                LessonPlanningRuleViolation(
                    code="LESSON_PLAN_PERIOD_INVALID",
                    message="Period plan must be within total_periods.",
                    field="periods",
                )
            )

        if period.period_in_lesson in period_numbers:
            violations.append(
                LessonPlanningRuleViolation(
                    code="LESSON_PERIOD_DUPLICATE",
                    message="Period numbers must be unique.",
                    field="periods",
                )
            )
        period_numbers.add(period.period_in_lesson)

        seen_orders: set[int] = set()
        for activity in period.activities:
            if activity.activity_id in activity_ids:
                violations.append(
                    LessonPlanningRuleViolation(
                        code="LESSON_ACTIVITY_ID_DUPLICATE",
                        message="Activity IDs must be unique in a lesson plan.",
                        field="periods.activities",
                    )
                )
            activity_ids.add(activity.activity_id)

            if activity.order in seen_orders:
                violations.append(
                    LessonPlanningRuleViolation(
                        code="LESSON_ACTIVITY_ORDER_DUPLICATE",
                        message=(
                            "Activity order values must be unique "
                            "within one period."
                        ),
                        field="periods.activities",
                    )
                )
            seen_orders.add(activity.order)

            for objective_ref in activity.objective_refs:
                if objective_ref not in objective_ids:
                    violations.append(
                        LessonPlanningRuleViolation(
                            code="LESSON_ACTIVITY_OBJECTIVE_REF_INVALID",
                            message=(
                                "Activity objective references must point "
                                "to lesson plan objectives."
                            ),
                            field="periods.activities",
                        )
                    )

            for resource_ref in activity.resource_refs:
                if resource_ref not in resource_ids:
                    violations.append(
                        LessonPlanningRuleViolation(
                            code="LESSON_ACTIVITY_RESOURCE_REF_INVALID",
                            message=(
                                "Activity resource references must point "
                                "to lesson plan resources."
                            ),
                            field="periods.activities",
                        )
                    )

    return tuple(violations)
