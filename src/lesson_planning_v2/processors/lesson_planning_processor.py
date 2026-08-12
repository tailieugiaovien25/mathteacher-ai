from __future__ import annotations

from typing import Any

from core_v2.processing import Processor
from educational_planning_v2.models import (
    EducationalPlan,
    EducationalPlanItem,
)
from lesson_planning_v2.builders import LessonPlanDraft
from lesson_planning_v2.lesson_planning import LessonPlanningFacade


class LessonPlanningProcessor(Processor):
    """Thin processor adapter for deterministic lesson-plan construction."""

    def __init__(
        self,
        facade: LessonPlanningFacade | None = None,
    ) -> None:
        self._facade = facade or LessonPlanningFacade()

    @property
    def processor_id(self) -> str:
        return "PROC-LESSON-PLANNING-V2"

    @property
    def data_type_id(self) -> str:
        return "LESSON_PLAN"

    @property
    def capability(self) -> str:
        return "BUILD_LESSON_PLAN"

    def process(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:
        if not isinstance(data, dict):
            raise TypeError("lesson planning input must be a dict")

        plan = data.get("educational_plan")
        if not isinstance(plan, EducationalPlan):
            raise TypeError(
                "educational_plan must be an EducationalPlan"
            )

        plan_item_id = data.get("plan_item_id")
        if not isinstance(plan_item_id, str) or not plan_item_id.strip():
            raise ValueError("plan_item_id is required")

        item = self._resolve_plan_item(
            plan=plan,
            plan_item_id=plan_item_id,
        )

        lesson_plan_id = data.get("lesson_plan_id")
        if not isinstance(lesson_plan_id, str) or not lesson_plan_id.strip():
            raise ValueError("lesson_plan_id is required")

        draft = self._to_draft(
            data.get("draft", LessonPlanDraft())
        )

        planning_context = self._facade.build_context(
            plan,
            item,
        )

        return self._facade.build_plan(
            lesson_plan_id=lesson_plan_id,
            context=planning_context,
            draft=draft,
        )

    @staticmethod
    def _resolve_plan_item(
        *,
        plan: EducationalPlan,
        plan_item_id: str,
    ) -> EducationalPlanItem:
        for item in plan.items:
            if item.plan_item_id == plan_item_id:
                return item

        raise LookupError(
            f"educational plan item not found: {plan_item_id}"
        )

    @staticmethod
    def _to_draft(data: Any) -> LessonPlanDraft:
        if isinstance(data, LessonPlanDraft):
            return data

        if not isinstance(data, dict):
            raise TypeError(
                "draft must be a dict or LessonPlanDraft"
            )

        return LessonPlanDraft(
            plan_mode=data.get("plan_mode", "FULL_LESSON"),
            period_in_lesson=data.get("period_in_lesson"),
            objectives=tuple(data.get("objectives", ())),
            resources=tuple(data.get("resources", ())),
            periods=tuple(data.get("periods", ())),
            status=data.get("status", "DRAFT"),
        )
