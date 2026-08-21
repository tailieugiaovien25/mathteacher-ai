from __future__ import annotations

from datetime import date
from typing import Any, Callable

from lesson_planning_v2.services.weekly_lesson_plan_grouping_service import (
    WeeklyLessonPlanGroup,
)
from lesson_planning_v2.weekly_lesson_plan_assembly import (
    WeeklyLessonPlan,
    WeeklyLessonPlanApproval,
    WeeklyLessonPlanSession,
)


PreparationDateResolver = Callable[
    [Any],
    date,
]


class WeeklyLessonPlanAssemblerService:
    def assemble(
        self,
        *,
        group: WeeklyLessonPlanGroup,
        preparation_date_resolver: PreparationDateResolver,
        approval: WeeklyLessonPlanApproval | None = None,
    ) -> WeeklyLessonPlan:
        items = tuple(group.items)

        if not items:
            raise ValueError(
                "group items must not be empty"
            )

        sessions = tuple(
            self._build_session(
                item=item,
                preparation_date_resolver=(
                    preparation_date_resolver
                ),
            )
            for item in items
        )

        return WeeklyLessonPlan(
            identity=group.identity,
            sessions=sessions,
            approval=approval,
        )

    def _build_session(
        self,
        *,
        item: Any,
        preparation_date_resolver: PreparationDateResolver,
    ) -> WeeklyLessonPlanSession:
        preparation_date = (
            preparation_date_resolver(
                item
            )
        )

        if not isinstance(
            preparation_date,
            date,
        ):
            raise ValueError(
                "preparation_date must be a date"
            )

        teaching_date = self._required_date(
            item=item,
            attribute="teaching_date",
        )

        period_number = self._required_positive_int(
            item=item,
            attribute="period_number",
        )

        curriculum_period = (
            self._required_positive_int(
                item=item,
                attribute="curriculum_period",
            )
        )

        lesson_title = self._required_text(
            item=item,
            attribute="lesson_title",
        )

        class_id = self._required_text(
            item=item,
            attribute="class_id",
        )

        component_ref = self._optional_text(
            getattr(
                item,
                "component_ref",
                None,
            )
        )

        return WeeklyLessonPlanSession(
            period_number=period_number,
            curriculum_period=curriculum_period,
            lesson_title=lesson_title,
            preparation_date=preparation_date,
            teaching_date=teaching_date,
            class_id=class_id,
            component_ref=component_ref,
        )

    @staticmethod
    def _required_positive_int(
        *,
        item: Any,
        attribute: str,
    ) -> int:
        try:
            value = getattr(
                item,
                attribute,
            )
        except AttributeError as error:
            raise ValueError(
                f"{attribute} is required"
            ) from error

        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise ValueError(
                f"{attribute} must be positive"
            )

        return value

    @staticmethod
    def _required_text(
        *,
        item: Any,
        attribute: str,
    ) -> str:
        try:
            value = getattr(
                item,
                attribute,
            )
        except AttributeError as error:
            raise ValueError(
                f"{attribute} is required"
            ) from error

        normalized = str(
            value or ""
        ).strip()

        if not normalized:
            raise ValueError(
                f"{attribute} must not be blank"
            )

        return normalized

    @staticmethod
    def _required_date(
        *,
        item: Any,
        attribute: str,
    ) -> date:
        try:
            value = getattr(
                item,
                attribute,
            )
        except AttributeError as error:
            raise ValueError(
                f"{attribute} is required"
            ) from error

        if not isinstance(
            value,
            date,
        ):
            raise ValueError(
                f"{attribute} must be a date"
            )

        return value

    @staticmethod
    def _optional_text(
        value: object,
    ) -> str | None:
        if value is None:
            return None

        normalized = str(
            value
        ).strip()

        if not normalized:
            return None

        return normalized
