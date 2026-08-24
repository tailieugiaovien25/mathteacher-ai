from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping

from lesson_planning_v2.weekly_lesson_plan_assembly import (
    WeeklyLessonPlanApproval,
)
from lesson_planning_v2.weekly_lesson_plan_identity import (
    WeeklyLessonPlanIdentity,
)


@dataclass(frozen=True)
class WeeklyLessonPlanContentSession:
    period_number: int
    curriculum_period: int
    lesson_title: str
    preparation_date: date
    teaching_date: date
    class_id: str
    content: Mapping[str, Any]
    component_ref: str | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.period_number, int)
            or isinstance(self.period_number, bool)
            or self.period_number <= 0
        ):
            raise ValueError(
                "period_number must be positive"
            )

        if (
            not isinstance(self.curriculum_period, int)
            or isinstance(self.curriculum_period, bool)
            or self.curriculum_period <= 0
        ):
            raise ValueError(
                "curriculum_period must be positive"
            )

        lesson_title = self._required_text(
            self.lesson_title,
            field_name="lesson_title",
        )

        class_id = self._required_text(
            self.class_id,
            field_name="class_id",
        )

        if not isinstance(
            self.preparation_date,
            date,
        ):
            raise ValueError(
                "preparation_date must be a date"
            )

        if not isinstance(
            self.teaching_date,
            date,
        ):
            raise ValueError(
                "teaching_date must be a date"
            )

        if (
            not isinstance(self.content, Mapping)
            or not self.content
        ):
            raise ValueError(
                "content must be a non-empty mapping"
            )

        component_ref = self._optional_text(
            self.component_ref
        )

        object.__setattr__(
            self,
            "lesson_title",
            lesson_title,
        )

        object.__setattr__(
            self,
            "class_id",
            class_id,
        )

        object.__setattr__(
            self,
            "component_ref",
            component_ref,
        )

    @staticmethod
    def _required_text(
        value: object,
        *,
        field_name: str,
    ) -> str:
        normalized = str(
            value or ""
        ).strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be blank"
            )

        return normalized

    @staticmethod
    def _optional_text(
        value: object,
    ) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()

        if not normalized:
            return None

        return normalized


@dataclass(frozen=True)
class WeeklyLessonPlanContent:
    identity: WeeklyLessonPlanIdentity
    sessions: tuple[
        WeeklyLessonPlanContentSession,
        ...
    ]
    approval: WeeklyLessonPlanApproval | None = None

    def __post_init__(self) -> None:
        sessions = tuple(
            self.sessions
        )

        if not sessions:
            raise ValueError(
                "sessions must not be empty"
            )

        ordered_sessions = tuple(
            sorted(
                sessions,
                key=self._session_sort_key,
            )
        )

        object.__setattr__(
            self,
            "sessions",
            ordered_sessions,
        )

    @staticmethod
    def _session_sort_key(
        session: WeeklyLessonPlanContentSession,
    ) -> tuple[
        int,
        date,
        str,
        int,
    ]:
        return (
            session.period_number,
            session.teaching_date,
            session.class_id,
            session.curriculum_period,
        )
