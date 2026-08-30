from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from lesson_planning_v2.models.lesson_plan_grouping import (
    LessonPlanGroupingMode,
    LessonPlanGroupingPolicy,
)


@dataclass(frozen=True, slots=True)
class LessonPlanGroupingPolicySource:
    exact: Mapping[tuple[str, str], LessonPlanGroupingMode]
    subject_defaults: Mapping[str, LessonPlanGroupingMode]
    fallback: LessonPlanGroupingMode = LessonPlanGroupingMode.BY_PERIOD

    def resolve(
        self,
        *,
        subject_ref: str,
        component_ref: str,
    ) -> LessonPlanGroupingPolicy:
        subject = str(subject_ref or "").strip()
        component = str(component_ref or "").strip()

        mode = self.exact.get((subject, component))
        if mode is None:
            mode = self.subject_defaults.get(subject, self.fallback)

        return LessonPlanGroupingPolicy(
            subject_ref=subject,
            component_ref=component,
            mode=mode,
        )

    @classmethod
    def safe_default(cls) -> "LessonPlanGroupingPolicySource":
        return cls(
            exact={},
            subject_defaults={},
            fallback=LessonPlanGroupingMode.BY_PERIOD,
        )
