from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from lesson_planning_v2.lesson_plan_selection_mode import (
    LessonPlanSelectionMode,
)
from lesson_planning_v2.weekly_lesson_plan_assembly import (
    WeeklyLessonPlanSession,
)


ContentMapping = Mapping[str, Any]

ContentProvider = Callable[
    [WeeklyLessonPlanSession],
    ContentMapping,
]


class WeeklyLessonPlanSelectionContentResolver:
    def __init__(
        self,
        *,
        lesson_provider: ContentProvider | None,
        period_provider: ContentProvider | None,
        topic_provider: ContentProvider | None,
    ) -> None:
        self._lesson_provider = lesson_provider
        self._period_provider = period_provider
        self._topic_provider = topic_provider

    def resolve(
        self,
        *,
        session: WeeklyLessonPlanSession,
        mode: LessonPlanSelectionMode,
    ) -> ContentMapping:
        provider = self._provider_for_mode(
            mode
        )

        content = provider(
            session
        )

        if (
            not isinstance(content, Mapping)
            or not content
        ):
            raise ValueError(
                "content must be a non-empty mapping"
            )

        return content

    def _provider_for_mode(
        self,
        mode: LessonPlanSelectionMode,
    ) -> ContentProvider:
        if mode == LessonPlanSelectionMode.LESSON:
            return self._required_provider(
                self._lesson_provider,
                provider_name="lesson_provider",
            )

        if mode == LessonPlanSelectionMode.PERIOD:
            return self._required_provider(
                self._period_provider,
                provider_name="period_provider",
            )

        if mode == LessonPlanSelectionMode.TOPIC:
            return self._required_provider(
                self._topic_provider,
                provider_name="topic_provider",
            )

        raise ValueError(
            "unsupported content selection mode"
        )

    @staticmethod
    def _required_provider(
        provider: ContentProvider | None,
        *,
        provider_name: str,
    ) -> ContentProvider:
        if provider is None:
            raise ValueError(
                f"{provider_name} is required"
            )

        return provider
