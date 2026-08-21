from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from lesson_planning_v2.services.lesson_schedule_source_adapter import (
    LessonScheduleSourceAdapter,
)


@dataclass(frozen=True)
class LessonPlanLessonTeachingDate:
    class_name: str
    teaching_date: date
    projected: bool = False


@dataclass(frozen=True)
class LessonPlanLessonOption:
    lesson_id: str
    lesson_title: str

    curriculum_periods: tuple[int, ...]
    total_periods: int

    class_names: tuple[str, ...]

    teaching_dates: tuple[
        LessonPlanLessonTeachingDate,
        ...
    ]

    has_projected_dates: bool

    @property
    def period_heading(self) -> str:
        return " + ".join(
            str(value)
            for value in self.curriculum_periods
        )

    @property
    def selection_label(self) -> str:
        periods = self.period_heading

        return (
            f"{self.lesson_title} "
            f"(Tiết {periods})"
        )


class LessonPlanLessonSelectorService:
    """
    Build lesson-level choices for the Teacher Portal.

    UI must choose a lesson, not an individual weekly
    schedule row.
    """

    def build_options(
        self,
        *,
        curriculum_periods: Iterable[object],
        schedules: Iterable[object],
        projected_schedule_ids: frozenset[str] = frozenset(),
    ) -> tuple[
        LessonPlanLessonOption,
        ...
    ]:
        curriculum_periods = tuple(
            curriculum_periods
        )

        schedules = tuple(
            schedules
        )

        source = (
            LessonScheduleSourceAdapter()
            .adapt(
                curriculum_periods=(
                    curriculum_periods
                ),
                schedules=schedules,
                projected_schedule_ids=(
                    projected_schedule_ids
                ),
            )
        )

        lesson_ids = tuple(
            sorted(
                {
                    row.lesson_id
                    for row
                    in source.curriculum_rows
                }
            )
        )

        options = []

        adapter = (
            LessonScheduleSourceAdapter()
        )

        for lesson_id in lesson_ids:
            try:
                aggregate = (
                    adapter.aggregate(
                        lesson_id=lesson_id,
                        curriculum_periods=(
                            curriculum_periods
                        ),
                        schedules=schedules,
                        projected_schedule_ids=(
                            projected_schedule_ids
                        ),
                    )
                )
            except ValueError as error:
                if (
                    "no teaching schedule"
                    in str(error)
                ):
                    continue

                raise

            options.append(
                LessonPlanLessonOption(
                    lesson_id=(
                        aggregate.lesson_id
                    ),
                    lesson_title=(
                        aggregate.lesson_title
                    ),
                    curriculum_periods=(
                        aggregate.curriculum_periods
                    ),
                    total_periods=(
                        aggregate.total_periods
                    ),
                    class_names=(
                        aggregate.class_names
                    ),
                    teaching_dates=tuple(
                        LessonPlanLessonTeachingDate(
                            class_name=(
                                occurrence.class_name
                            ),
                            teaching_date=(
                                occurrence.teaching_date
                            ),
                            projected=(
                                occurrence.projected
                            ),
                        )
                        for occurrence
                        in aggregate.teaching_occurrences
                    ),
                    has_projected_dates=(
                        aggregate.has_projected_dates
                    ),
                )
            )

        return tuple(
            sorted(
                options,
                key=lambda item: (
                    item.curriculum_periods[0],
                    item.lesson_title,
                ),
            )
        )

    def get_option(
        self,
        *,
        lesson_id: str,
        curriculum_periods: Iterable[object],
        schedules: Iterable[object],
        projected_schedule_ids: frozenset[str] = frozenset(),
    ) -> LessonPlanLessonOption:
        normalized_lesson_id = (
            lesson_id.strip()
        )

        if not normalized_lesson_id:
            raise ValueError(
                "lesson_id must not be blank"
            )

        options = self.build_options(
            curriculum_periods=(
                curriculum_periods
            ),
            schedules=schedules,
            projected_schedule_ids=(
                projected_schedule_ids
            ),
        )

        for option in options:
            if (
                option.lesson_id
                == normalized_lesson_id
            ):
                return option

        raise ValueError(
            "lesson option not found"
        )
