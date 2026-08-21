from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from lesson_planning_v2.services.lesson_plan_template_application_service import (
    LessonTeachingOccurrence,
)


@dataclass(frozen=True)
class LessonCurriculumPeriod:
    """
    One curriculum period belonging to one lesson.

    lesson_id is the canonical identity used for grouping.
    """

    lesson_id: str
    lesson_title: str
    curriculum_period: int
    period_in_lesson: int
    total_periods: int

    def __post_init__(self) -> None:
        if not self.lesson_id.strip():
            raise ValueError(
                "lesson_id must not be blank"
            )

        if not self.lesson_title.strip():
            raise ValueError(
                "lesson_title must not be blank"
            )

        if self.curriculum_period <= 0:
            raise ValueError(
                "curriculum_period must be positive"
            )

        if self.period_in_lesson <= 0:
            raise ValueError(
                "period_in_lesson must be positive"
            )

        if self.total_periods <= 0:
            raise ValueError(
                "total_periods must be positive"
            )

        if self.period_in_lesson > self.total_periods:
            raise ValueError(
                "period_in_lesson must not exceed "
                "total_periods"
            )


@dataclass(frozen=True)
class ScheduledLessonPeriod:
    """
    One scheduled teaching occurrence of a PPCT period.

    projected=True marks a teaching date inferred from a
    previous/current timetable rather than confirmed schedule.
    """

    lesson_id: str
    curriculum_period: int
    class_name: str
    teaching_date: date
    projected: bool = False

    def __post_init__(self) -> None:
        if not self.lesson_id.strip():
            raise ValueError(
                "lesson_id must not be blank"
            )

        if self.curriculum_period <= 0:
            raise ValueError(
                "curriculum_period must be positive"
            )

        if not self.class_name.strip():
            raise ValueError(
                "class_name must not be blank"
            )


@dataclass(frozen=True)
class LessonScheduleAggregate:
    lesson_id: str
    lesson_title: str

    curriculum_periods: tuple[int, ...]
    total_periods: int

    class_names: tuple[str, ...]

    teaching_occurrences: tuple[
        LessonTeachingOccurrence,
        ...
    ]

    has_projected_dates: bool


class LessonScheduleAggregator:
    """
    Aggregate PPCT + teaching schedule at LESSON level.

    The teacher selects a lesson, not an individual period.

    Aggregation rules:
    - group by canonical lesson_id;
    - collect all PPCT periods of the lesson;
    - collect all classes teaching the lesson;
    - preserve teaching dates even when they fall in a later week;
    - prefer confirmed dates over projected duplicates;
    - return one lesson-level aggregate.
    """

    def aggregate(
        self,
        *,
        lesson_id: str,
        curriculum_rows: tuple[
            LessonCurriculumPeriod,
            ...
        ],
        schedule_rows: tuple[
            ScheduledLessonPeriod,
            ...
        ],
    ) -> LessonScheduleAggregate:
        normalized_lesson_id = (
            lesson_id.strip()
        )

        if not normalized_lesson_id:
            raise ValueError(
                "lesson_id must not be blank"
            )

        lesson_curriculum_rows = tuple(
            row
            for row in curriculum_rows
            if row.lesson_id
            == normalized_lesson_id
        )

        if not lesson_curriculum_rows:
            raise ValueError(
                "lesson not found in curriculum"
            )

        self._validate_curriculum_rows(
            lesson_curriculum_rows
        )

        curriculum_periods = tuple(
            sorted(
                {
                    row.curriculum_period
                    for row
                    in lesson_curriculum_rows
                }
            )
        )

        lesson_title = (
            lesson_curriculum_rows[0]
            .lesson_title
            .strip()
        )

        total_periods = (
            lesson_curriculum_rows[0]
            .total_periods
        )

        lesson_schedule_rows = tuple(
            row
            for row in schedule_rows
            if (
                row.lesson_id
                == normalized_lesson_id
                and row.curriculum_period
                in curriculum_periods
            )
        )

        if not lesson_schedule_rows:
            raise ValueError(
                "lesson has no teaching schedule"
            )

        normalized_schedule_rows = (
            self._prefer_confirmed_rows(
                lesson_schedule_rows
            )
        )

        class_names = tuple(
            sorted(
                {
                    row.class_name.strip()
                    for row
                    in normalized_schedule_rows
                }
            )
        )

        teaching_occurrences = (
            self._build_occurrences(
                normalized_schedule_rows
            )
        )

        return LessonScheduleAggregate(
            lesson_id=normalized_lesson_id,
            lesson_title=lesson_title,
            curriculum_periods=(
                curriculum_periods
            ),
            total_periods=total_periods,
            class_names=class_names,
            teaching_occurrences=(
                teaching_occurrences
            ),
            has_projected_dates=any(
                occurrence.projected
                for occurrence
                in teaching_occurrences
            ),
        )

    @staticmethod
    def _validate_curriculum_rows(
        rows: tuple[
            LessonCurriculumPeriod,
            ...
        ],
    ) -> None:
        lesson_titles = {
            row.lesson_title.strip()
            for row in rows
        }

        if len(lesson_titles) != 1:
            raise ValueError(
                "lesson curriculum rows "
                "must have one lesson title"
            )

        total_period_values = {
            row.total_periods
            for row in rows
        }

        if len(total_period_values) != 1:
            raise ValueError(
                "lesson curriculum rows "
                "must have one total_periods value"
            )

        total_periods = next(
            iter(total_period_values)
        )

        period_in_lesson_values = {
            row.period_in_lesson
            for row in rows
        }

        expected = set(
            range(
                1,
                total_periods + 1,
            )
        )

        if period_in_lesson_values != expected:
            raise ValueError(
                "lesson curriculum periods "
                "are incomplete"
            )

    @staticmethod
    def _prefer_confirmed_rows(
        rows: tuple[
            ScheduledLessonPeriod,
            ...
        ],
    ) -> tuple[
        ScheduledLessonPeriod,
        ...
    ]:
        """
        Deduplicate exact class/period/date collisions.

        Confirmed schedule wins over projected schedule.
        """

        selected = {}

        for row in rows:
            key = (
                row.class_name.strip(),
                row.curriculum_period,
                row.teaching_date,
            )

            current = selected.get(
                key
            )

            if current is None:
                selected[key] = row
                continue

            if (
                current.projected
                and not row.projected
            ):
                selected[key] = row

        return tuple(
            sorted(
                selected.values(),
                key=lambda item: (
                    item.teaching_date,
                    item.class_name,
                    item.curriculum_period,
                ),
            )
        )

    @staticmethod
    def _build_occurrences(
        rows: tuple[
            ScheduledLessonPeriod,
            ...
        ],
    ) -> tuple[
        LessonTeachingOccurrence,
        ...
    ]:
        """
        Lesson metadata needs one teaching-date line for each
        class/date combination, not one line per PPCT period.

        Therefore two periods of the same lesson taught to the
        same class on the same date produce one occurrence.
        """

        selected = {}

        for row in rows:
            key = (
                row.class_name.strip(),
                row.teaching_date,
            )

            current = selected.get(
                key
            )

            if current is None:
                selected[key] = (
                    LessonTeachingOccurrence(
                        class_name=(
                            row.class_name.strip()
                        ),
                        teaching_date=(
                            row.teaching_date
                        ),
                        projected=row.projected,
                    )
                )
                continue

            if (
                current.projected
                and not row.projected
            ):
                selected[key] = (
                    LessonTeachingOccurrence(
                        class_name=(
                            row.class_name.strip()
                        ),
                        teaching_date=(
                            row.teaching_date
                        ),
                        projected=False,
                    )
                )

        return tuple(
            sorted(
                selected.values(),
                key=lambda item: (
                    item.teaching_date,
                    item.class_name,
                ),
            )
        )
