from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any


class LessonPlanGroupValidationError(ValueError):
    pass


class LessonPlanGroupingMode(str, Enum):
    BY_PERIOD = "BY_PERIOD"
    BY_LESSON = "BY_LESSON"
    BY_WEEK = "BY_WEEK"
    BY_GRADE = "BY_GRADE"


@dataclass(frozen=True, slots=True)
class TeachingOccurrence:
    row_index: int
    class_id: str
    teaching_date: date | Any | None
    timetable_period: int | Any | None
    timetable_slot_id: str | None
    curriculum_period: int | Any | None


@dataclass(frozen=True, slots=True)
class LessonPlanGroupingPolicy:
    subject_ref: str
    component_ref: str
    mode: LessonPlanGroupingMode


@dataclass(frozen=True, slots=True)
class LessonPlanGroup:
    group_id: str
    grouping_mode: LessonPlanGroupingMode
    subject_ref: str
    component_ref: str
    grade: int | None
    lesson_id: str | None
    lesson_title: str
    curriculum_periods: tuple
    occurrences: tuple[TeachingOccurrence, ...]
    representative_row_index: int
    source: str = "LBG_PBSDTB"

    @property
    def class_ids(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(
            item.class_id for item in self.occurrences if item.class_id
        ))

    @property
    def teaching_dates_by_class(self) -> tuple[tuple[str, Any], ...]:
        return tuple(
            (item.class_id, item.teaching_date)
            for item in self.occurrences
            if item.class_id and item.teaching_date is not None
        )

    @property
    def timetable_periods_by_class(self) -> tuple[tuple[str, Any], ...]:
        return tuple(
            (item.class_id, item.timetable_period)
            for item in self.occurrences
            if item.class_id and item.timetable_period is not None
        )
