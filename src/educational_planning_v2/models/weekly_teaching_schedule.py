from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} must not be empty")

    return normalized


def _optional_text(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")

    normalized = value.strip()
    return normalized or None


def _positive_int(value: int, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{field_name} must be an int")

    if value <= 0:
        raise ValueError(f"{field_name} must be positive")

    return value


@dataclass(frozen=True)
class AcademicWeek:
    academic_year: str
    week_number: int
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "academic_year",
            _required_text(self.academic_year, "academic_year"),
        )
        _positive_int(self.week_number, "week_number")

        if not isinstance(self.start_date, date):
            raise TypeError("start_date must be a date")

        if not isinstance(self.end_date, date):
            raise TypeError("end_date must be a date")

        if self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date")


@dataclass(frozen=True)
class TimetableSlot:
    teacher_id: str
    class_id: str
    subject_ref: str
    weekday: int
    timetable_period: int
    effective_from: date
    effective_to: date
    component_ref: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("teacher_id", "class_id", "subject_ref"):
            object.__setattr__(
                self,
                field_name,
                _required_text(getattr(self, field_name), field_name),
            )

        object.__setattr__(
            self,
            "component_ref",
            _optional_text(self.component_ref, "component_ref"),
        )
        _positive_int(self.timetable_period, "timetable_period")

        if not isinstance(self.weekday, int) or isinstance(self.weekday, bool):
            raise TypeError("weekday must be an int")

        if self.weekday < 1 or self.weekday > 7:
            raise ValueError("weekday must be between 1 and 7")

        if not isinstance(self.effective_from, date):
            raise TypeError("effective_from must be a date")

        if not isinstance(self.effective_to, date):
            raise TypeError("effective_to must be a date")

        if self.effective_from > self.effective_to:
            raise ValueError("effective_from must not be after effective_to")

    @property
    def curriculum_key(self) -> tuple[str, str, str | None]:
        return self.class_id, self.subject_ref, self.component_ref


@dataclass(frozen=True)
class CurriculumPeriod:
    class_id: str
    subject_ref: str
    period_number: int
    lesson_id: str
    lesson_title: str
    component_ref: str | None = None
    period_in_lesson: int = 1
    total_lesson_periods: int = 1
    teaching_equipment: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "class_id",
            "subject_ref",
            "lesson_id",
            "lesson_title",
        ):
            object.__setattr__(
                self,
                field_name,
                _required_text(getattr(self, field_name), field_name),
            )

        object.__setattr__(
            self,
            "component_ref",
            _optional_text(self.component_ref, "component_ref"),
        )
        _positive_int(self.period_number, "period_number")
        _positive_int(self.period_in_lesson, "period_in_lesson")
        _positive_int(self.total_lesson_periods, "total_lesson_periods")

        if self.period_in_lesson > self.total_lesson_periods:
            raise ValueError(
                "period_in_lesson must not exceed total_lesson_periods"
            )

        if not isinstance(self.teaching_equipment, tuple):
            raise TypeError("teaching_equipment must be a tuple")

        normalized_equipment = tuple(
            _required_text(item, "teaching_equipment item")
            for item in self.teaching_equipment
        )
        object.__setattr__(self, "teaching_equipment", normalized_equipment)

    @property
    def curriculum_key(self) -> tuple[str, str, str | None]:
        return self.class_id, self.subject_ref, self.component_ref


@dataclass(frozen=True)
class LessonExecutionRecord:
    teacher_id: str
    class_id: str
    subject_ref: str
    teaching_date: date
    curriculum_period: int
    status: str
    component_ref: str | None = None

    _COMPLETED_STATUS = "COMPLETED"

    def __post_init__(self) -> None:
        for field_name in ("teacher_id", "class_id", "subject_ref", "status"):
            object.__setattr__(
                self,
                field_name,
                _required_text(getattr(self, field_name), field_name),
            )

        object.__setattr__(self, "status", self.status.upper())
        object.__setattr__(
            self,
            "component_ref",
            _optional_text(self.component_ref, "component_ref"),
        )
        _positive_int(self.curriculum_period, "curriculum_period")

        if not isinstance(self.teaching_date, date):
            raise TypeError("teaching_date must be a date")

    @property
    def curriculum_key(self) -> tuple[str, str, str | None]:
        return self.class_id, self.subject_ref, self.component_ref

    @property
    def is_completed(self) -> bool:
        return self.status == self._COMPLETED_STATUS


@dataclass(frozen=True)
class WeeklyTeachingScheduleEntry:
    teaching_date: date
    weekday: int
    timetable_period: int
    teacher_id: str
    class_id: str
    subject_ref: str
    curriculum_period: int
    lesson_id: str
    lesson_title: str
    component_ref: str | None = None
    period_in_lesson: int = 1
    total_lesson_periods: int = 1
    teaching_equipment: tuple[str, ...] = ()


@dataclass(frozen=True)
class WeeklyTeachingSchedule:
    schedule_id: str
    teacher_id: str
    academic_week: AcademicWeek
    entries: tuple[WeeklyTeachingScheduleEntry, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schedule_id",
            _required_text(self.schedule_id, "schedule_id"),
        )
        object.__setattr__(
            self,
            "teacher_id",
            _required_text(self.teacher_id, "teacher_id"),
        )

        if not isinstance(self.academic_week, AcademicWeek):
            raise TypeError("academic_week must be an AcademicWeek")

        if not isinstance(self.entries, tuple):
            raise TypeError("entries must be a tuple")

        if not all(
            isinstance(entry, WeeklyTeachingScheduleEntry)
            for entry in self.entries
        ):
            raise TypeError(
                "all entries must be WeeklyTeachingScheduleEntry instances"
            )

        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a dict")

        object.__setattr__(self, "metadata", dict(self.metadata))
