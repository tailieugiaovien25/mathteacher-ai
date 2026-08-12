from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from lesson_planning_v2.contexts import LessonPlanningContext
from lesson_planning_v2.models import (
    LearningActivity,
    LessonObjective,
    LessonPlan,
    PeriodPlan,
    TeachingResource,
)
from lesson_planning_v2.validators import LessonPlanValidator


@dataclass(frozen=True)
class LessonPlanDraft:
    """Input contract used to construct one canonical lesson plan."""

    plan_mode: str = "FULL_LESSON"
    period_in_lesson: int | None = None

    objectives: tuple[LessonObjective, ...] = ()
    resources: tuple[TeachingResource, ...] = ()
    periods: tuple[PeriodPlan, ...] = ()

    status: str = "DRAFT"
    metadata: dict[str, Any] = field(default_factory=dict)


class LessonPlanBuilder:
    """Build a validated canonical lesson plan from trusted context."""

    def __init__(
        self,
        validator: LessonPlanValidator | None = None,
    ) -> None:
        self._validator = validator or LessonPlanValidator()

    def build(
        self,
        *,
        lesson_plan_id: str,
        context: LessonPlanningContext,
        draft: LessonPlanDraft,
    ) -> LessonPlan:
        plan = LessonPlan(
            lesson_plan_id=lesson_plan_id,
            educational_plan_id=context.educational_plan_id,
            plan_item_id=context.plan_item_id,
            curriculum_ref=context.curriculum_scope.curriculum_ref,
            grade=context.grade,
            title=context.title,
            plan_mode=draft.plan_mode,
            total_periods=context.periods,
            period_in_lesson=draft.period_in_lesson,
            curriculum_node_refs=tuple(
                node.curriculum_node_id
                for node in context.nodes
            ),
            canonical_requirement_refs=tuple(
                requirement.canonical_id
                for requirement in context.requirements
            ),
            objectives=draft.objectives,
            resources=draft.resources,
            periods=draft.periods,
            status=draft.status,
            metadata=dict(draft.metadata),
        )

        result = self._validator.validate(plan)
        if not result.is_valid:
            details = "; ".join(
                f"{issue.code}: {issue.message}"
                for issue in result.issues
            )
            raise ValueError(
                f"Lesson plan is invalid: {details}"
            )

        return plan


def get_lesson_plan_builder() -> LessonPlanBuilder:
    return LessonPlanBuilder()
