from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class AcademicYearCalendarEventType(
    str,
    Enum,
):
    HOLIDAY = "HOLIDAY"
    TET_BREAK = "TET_BREAK"
    MIDTERM_BREAK = "MIDTERM_BREAK"
    MAKEUP_DAY = "MAKEUP_DAY"
    SCHOOL_EVENT = "SCHOOL_EVENT"
    OTHER_BREAK = "OTHER_BREAK"


class AcademicYearCalendarEventStatus(
    str,
    Enum,
):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@dataclass(frozen=True)
class AcademicYearCalendarEvent:
    event_id: str
    academic_year_id: str
    event_type: AcademicYearCalendarEventType
    name: str
    start_date: date
    end_date: date
    is_teaching_day_override: bool = False
    note: str | None = None
    status: AcademicYearCalendarEventStatus = (
        AcademicYearCalendarEventStatus.ACTIVE
    )

    def __post_init__(self) -> None:
        for field_name in (
            "event_id",
            "academic_year_id",
            "name",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                str,
            ):
                raise TypeError(
                    f"{field_name} must be str"
                )

            normalized = (
                value.strip()
            )

            if not normalized:
                raise ValueError(
                    f"{field_name} must not be empty"
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )

        if not isinstance(
            self.event_type,
            AcademicYearCalendarEventType,
        ):
            raise TypeError(
                "event_type must be "
                "AcademicYearCalendarEventType"
            )

        if not isinstance(
            self.start_date,
            date,
        ):
            raise TypeError(
                "start_date must be date"
            )

        if not isinstance(
            self.end_date,
            date,
        ):
            raise TypeError(
                "end_date must be date"
            )

        if self.start_date > self.end_date:
            raise ValueError(
                "start_date must not be "
                "after end_date"
            )

        if not isinstance(
            self.is_teaching_day_override,
            bool,
        ):
            raise TypeError(
                "is_teaching_day_override "
                "must be bool"
            )

        if self.note is not None:
            if not isinstance(
                self.note,
                str,
            ):
                raise TypeError(
                    "note must be str or None"
                )

            normalized_note = (
                self.note.strip()
            )

            object.__setattr__(
                self,
                "note",
                normalized_note
                or None,
            )

        if not isinstance(
            self.status,
            AcademicYearCalendarEventStatus,
        ):
            raise TypeError(
                "status must be "
                "AcademicYearCalendarEventStatus"
            )

        if (
            self.event_type
            is AcademicYearCalendarEventType.MAKEUP_DAY
            and not self.is_teaching_day_override
        ):
            raise ValueError(
                "MAKEUP_DAY must define "
                "is_teaching_day_override=True"
            )

        if (
            self.event_type
            is not AcademicYearCalendarEventType.MAKEUP_DAY
            and self.is_teaching_day_override
        ):
            raise ValueError(
                "only MAKEUP_DAY may define "
                "is_teaching_day_override=True"
            )
