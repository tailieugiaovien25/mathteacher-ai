from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from lesson_planning_v2.lesson_plan_teaching_scope import (
    LessonPlanTeachingScope,
)
from lesson_planning_v2.weekly_lesson_plan_identity import (
    WeeklyLessonPlanIdentity,
)


@dataclass(frozen=True)
class WeeklyLessonPlanGroup:
    identity: WeeklyLessonPlanIdentity
    items: tuple[Any, ...]


class WeeklyLessonPlanGroupingService:
    def group_for_class(
        self,
        *,
        items: Iterable[Any],
    ) -> tuple[WeeklyLessonPlanGroup, ...]:
        return self._group(
            items=items,
            scope_factory=self._class_scope,
        )

    def group_for_grade(
        self,
        *,
        items: Iterable[Any],
    ) -> tuple[WeeklyLessonPlanGroup, ...]:
        return self._group(
            items=items,
            scope_factory=self._grade_scope,
        )

    def _group(
        self,
        *,
        items: Iterable[Any],
        scope_factory: Callable[
            [Any],
            LessonPlanTeachingScope,
        ],
    ) -> tuple[WeeklyLessonPlanGroup, ...]:
        grouped: dict[
            tuple[
                str,
                str,
                int,
                str,
                str,
                str,
            ],
            list[Any],
        ] = {}

        identities: dict[
            tuple[
                str,
                str,
                int,
                str,
                str,
                str,
            ],
            WeeklyLessonPlanIdentity,
        ] = {}

        for item in items:
            identity = self._identity(
                item=item,
                scope=scope_factory(item),
            )

            key = identity.identity_key

            if key not in grouped:
                grouped[key] = []
                identities[key] = identity

            grouped[key].append(item)

        result: list[
            WeeklyLessonPlanGroup
        ] = []

        for key, grouped_items in grouped.items():
            ordered_items = tuple(
                sorted(
                    grouped_items,
                    key=self._item_sort_key,
                )
            )

            result.append(
                WeeklyLessonPlanGroup(
                    identity=identities[key],
                    items=ordered_items,
                )
            )

        result.sort(
            key=self._group_sort_key
        )

        return tuple(result)

    def _identity(
        self,
        *,
        item: Any,
        scope: LessonPlanTeachingScope,
    ) -> WeeklyLessonPlanIdentity:
        return WeeklyLessonPlanIdentity(
            teacher_id=self._required_text(
                item=item,
                attribute="teacher_id",
            ),
            academic_year=self._required_text(
                item=item,
                attribute="academic_year",
            ),
            week_number=self._required_week(
                item=item,
            ),
            subject_ref=self._required_text(
                item=item,
                attribute="subject_ref",
            ),
            teaching_scope=scope,
        )

    def _class_scope(
        self,
        item: Any,
    ) -> LessonPlanTeachingScope:
        return LessonPlanTeachingScope.for_class(
            class_id=self._required_text(
                item=item,
                attribute="class_id",
            ),
        )

    def _grade_scope(
        self,
        item: Any,
    ) -> LessonPlanTeachingScope:
        return LessonPlanTeachingScope.for_grade(
            grade_key=self._required_text(
                item=item,
                attribute="grade_key",
            ),
        )

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
    def _required_week(
        *,
        item: Any,
    ) -> int:
        try:
            value = item.week_number
        except AttributeError as error:
            raise ValueError(
                "week_number is required"
            ) from error

        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise ValueError(
                "week_number must be positive"
            )

        return value

    @staticmethod
    def _item_sort_key(
        item: Any,
    ) -> tuple[int, str, str]:
        period_number = getattr(
            item,
            "period_number",
            0,
        )

        if (
            not isinstance(period_number, int)
            or isinstance(period_number, bool)
        ):
            period_number = 0

        class_id = str(
            getattr(
                item,
                "class_id",
                "",
            )
            or ""
        )

        lesson_title = str(
            getattr(
                item,
                "lesson_title",
                "",
            )
            or ""
        )

        return (
            period_number,
            class_id,
            lesson_title,
        )

    @staticmethod
    def _group_sort_key(
        group: WeeklyLessonPlanGroup,
    ) -> tuple[
        str,
        str,
        int,
        str,
        str,
        str,
    ]:
        return group.identity.identity_key
