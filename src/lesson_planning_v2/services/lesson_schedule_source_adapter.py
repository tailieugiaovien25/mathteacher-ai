from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from lesson_planning_v2.services.lesson_schedule_aggregator import (
    LessonCurriculumPeriod,
    LessonScheduleAggregate,
    LessonScheduleAggregator,
    ScheduledLessonPeriod,
)


@dataclass(frozen=True)
class LessonScheduleSourceData:
    """
    Normalized input for lesson-level aggregation.

    The source adapter deliberately does not depend on
    Supabase, Excel, or a physical repository.
    """

    curriculum_rows: tuple[
        LessonCurriculumPeriod,
        ...
    ]

    schedule_rows: tuple[
        ScheduledLessonPeriod,
        ...
    ]


class LessonScheduleSourceAdapter:
    """
    Bridge existing PPCT + WeeklyTeachingSchedule objects
    into LessonScheduleAggregator.

    Existing system contract:

    PPCT / CurriculumPeriod supplies:
    - class_id
    - period_number
    - lesson_id
    - lesson_title
    - period_in_lesson

    Weekly schedule entry supplies:
    - class_id
    - curriculum_period
    - teaching_date

    Therefore no lesson identity is inferred from free text.
    lesson_id always comes from PPCT.
    """

    def adapt(
        self,
        *,
        curriculum_periods: Iterable[object],
        schedules: Iterable[object],
        projected_schedule_ids: frozenset[str] = frozenset(),
    ) -> LessonScheduleSourceData:
        curriculum_periods = tuple(
            curriculum_periods
        )

        schedules = tuple(
            schedules
        )

        if not curriculum_periods:
            raise ValueError(
                "curriculum_periods must not be empty"
            )

        curriculum_index = (
            self._build_curriculum_index(
                curriculum_periods
            )
        )

        lesson_rows = (
            self._build_lesson_rows(
                curriculum_periods
            )
        )

        schedule_rows = (
            self._build_schedule_rows(
                schedules=schedules,
                curriculum_index=(
                    curriculum_index
                ),
                projected_schedule_ids=(
                    projected_schedule_ids
                ),
            )
        )

        return LessonScheduleSourceData(
            curriculum_rows=lesson_rows,
            schedule_rows=schedule_rows,
        )

    def aggregate(
        self,
        *,
        lesson_id: str,
        curriculum_periods: Iterable[object],
        schedules: Iterable[object],
        projected_schedule_ids: frozenset[str] = frozenset(),
    ) -> LessonScheduleAggregate:
        source = self.adapt(
            curriculum_periods=(
                curriculum_periods
            ),
            schedules=schedules,
            projected_schedule_ids=(
                projected_schedule_ids
            ),
        )

        return LessonScheduleAggregator().aggregate(
            lesson_id=lesson_id,
            curriculum_rows=(
                source.curriculum_rows
            ),
            schedule_rows=(
                source.schedule_rows
            ),
        )

    @staticmethod
    def _build_curriculum_index(
        curriculum_periods: tuple[
            object,
            ...
        ],
    ) -> dict[
        tuple[str, int],
        object,
    ]:
        index = {}

        for row in curriculum_periods:
            class_id = (
                str(
                    getattr(
                        row,
                        "class_id",
                    )
                ).strip()
            )

            period_number = int(
                getattr(
                    row,
                    "period_number",
                )
            )

            if not class_id:
                raise ValueError(
                    "curriculum class_id "
                    "must not be blank"
                )

            key = (
                class_id,
                period_number,
            )

            if key in index:
                raise ValueError(
                    "duplicate curriculum "
                    "class/period"
                )

            index[key] = row

        return index

    @staticmethod
    def _build_lesson_rows(
        curriculum_periods: tuple[
            object,
            ...
        ],
    ) -> tuple[
        LessonCurriculumPeriod,
        ...
    ]:
        grouped = {}

        for source in curriculum_periods:
            lesson_id = (
                str(
                    getattr(
                        source,
                        "lesson_id",
                    )
                ).strip()
            )

            lesson_title = (
                str(
                    getattr(
                        source,
                        "lesson_title",
                    )
                ).strip()
            )

            period_number = int(
                getattr(
                    source,
                    "period_number",
                )
            )

            period_in_lesson = int(
                getattr(
                    source,
                    "period_in_lesson",
                    1,
                )
                or 1
            )

            key = (
                lesson_id,
                period_number,
            )

            grouped[key] = (
                lesson_title,
                period_in_lesson,
            )

        total_by_lesson = {}

        for (
            lesson_id,
            _period_number,
        ), (
            _title,
            period_in_lesson,
        ) in grouped.items():
            total_by_lesson[
                lesson_id
            ] = max(
                total_by_lesson.get(
                    lesson_id,
                    0,
                ),
                period_in_lesson,
            )

        return tuple(
            LessonCurriculumPeriod(
                lesson_id=lesson_id,
                lesson_title=lesson_title,
                curriculum_period=(
                    period_number
                ),
                period_in_lesson=(
                    period_in_lesson
                ),
                total_periods=(
                    total_by_lesson[
                        lesson_id
                    ]
                ),
            )
            for (
                lesson_id,
                period_number,
            ), (
                lesson_title,
                period_in_lesson,
            ) in sorted(
                grouped.items(),
                key=lambda item: (
                    item[0][0],
                    item[0][1],
                ),
            )
        )

    @staticmethod
    def _build_schedule_rows(
        *,
        schedules: tuple[
            object,
            ...
        ],
        curriculum_index: dict[
            tuple[str, int],
            object,
        ],
        projected_schedule_ids: frozenset[
            str
        ],
    ) -> tuple[
        ScheduledLessonPeriod,
        ...
    ]:
        result = []

        for schedule in schedules:
            schedule_id = str(
                getattr(
                    schedule,
                    "schedule_id",
                    "",
                )
            )

            projected = (
                schedule_id
                in projected_schedule_ids
            )

            entries = tuple(
                getattr(
                    schedule,
                    "entries",
                    (),
                )
            )

            for entry in entries:
                class_id = (
                    str(
                        getattr(
                            entry,
                            "class_id",
                        )
                    ).strip()
                )

                curriculum_period = int(
                    getattr(
                        entry,
                        "curriculum_period",
                    )
                )

                key = (
                    class_id,
                    curriculum_period,
                )

                curriculum = (
                    curriculum_index.get(
                        key
                    )
                )

                if curriculum is None:
                    # Schedule row outside the supplied
                    # PPCT scope is irrelevant here.
                    continue

                lesson_id = str(
                    getattr(
                        curriculum,
                        "lesson_id",
                    )
                ).strip()

                result.append(
                    ScheduledLessonPeriod(
                        lesson_id=lesson_id,
                        curriculum_period=(
                            curriculum_period
                        ),
                        class_name=class_id,
                        teaching_date=(
                            getattr(
                                entry,
                                "teaching_date",
                            )
                        ),
                        projected=projected,
                    )
                )

        if not result:
            raise ValueError(
                "no schedule rows matched "
                "the supplied curriculum"
            )

        return tuple(result)
