from __future__ import annotations

from collections.abc import Iterable

from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroupingMode
from lesson_planning_v2.models.lesson_plan_grouping_policy_config import (
    LessonPlanGroupingPolicyConfig,
)
from lesson_planning_v2.services.lesson_plan_grouping_policy_source import (
    LessonPlanGroupingPolicySource,
)


class LessonPlanGroupingPolicyConfigService:
    def build_policy_source(
        self,
        configs: Iterable[LessonPlanGroupingPolicyConfig],
        *,
        fallback: LessonPlanGroupingMode = LessonPlanGroupingMode.BY_PERIOD,
    ) -> LessonPlanGroupingPolicySource:
        exact: dict[tuple[str, str], LessonPlanGroupingMode] = {}
        subject_defaults: dict[str, LessonPlanGroupingMode] = {}

        for config in configs:
            if not config.active:
                continue

            key = (config.subject_ref, config.component_ref)
            if config.component_ref:
                exact[key] = config.mode
            else:
                subject_defaults[config.subject_ref] = config.mode

        return LessonPlanGroupingPolicySource(
            exact=exact,
            subject_defaults=subject_defaults,
            fallback=fallback,
        )
