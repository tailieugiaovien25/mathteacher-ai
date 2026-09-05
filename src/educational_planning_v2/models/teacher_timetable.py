from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class TeachingSession(str, Enum):
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"


class TeacherTimetableSlotStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


def _required_text(
    value: str,
    field_name: str,
    maximum: int = 250,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{field_name} must not be empty"
        )

    if len(normalized) > maximum:
        raise ValueError(
            f"{field_name} must not exceed "
            f"{maximum} characters"
        )

    return normalized


@dataclass(frozen=True)
class TeacherTimetableSlot:
    slot_id: str
    owner_id: str
    academic_year: str
    assignment_id: str
    weekday: int
    session: TeachingSession
    period: int
    effective_from: date
    effective_to: date
    status: TeacherTimetableSlotStatus = (
        TeacherTimetableSlotStatus.ACTIVE
    )
    # V14B6K_TIMETABLE_COMPONENT_SCOPE
    component_id: str | None = None

    def __post_init__(self) -> None:
        for field_name, maximum in (
            ("slot_id", 120),
            ("owner_id", 120),
            ("academic_year", 30),
            ("assignment_id", 120),
        ):
            object.__setattr__(
                self,
                field_name,
                _required_text(
                    getattr(self, field_name),
                    field_name,
                    maximum,
                ),
            )

        if (
            not isinstance(self.weekday, int)
            or isinstance(self.weekday, bool)
        ):
            raise TypeError(
                "weekday must be an int"
            )

        if self.weekday < 1 or self.weekday > 7:
            raise ValueError(
                "weekday must be between 1 and 7"
            )

        if not isinstance(
            self.session,
            TeachingSession,
        ):
            raise TypeError(
                "session must be TeachingSession"
            )

        if (
            not isinstance(self.period, int)
            or isinstance(self.period, bool)
        ):
            raise TypeError(
                "period must be an int"
            )

        if self.period < 1 or self.period > 5:
            raise ValueError(
                "period must be between 1 and 5"
            )

        if not isinstance(
            self.effective_from,
            date,
        ):
            raise TypeError(
                "effective_from must be a date"
            )

        if not isinstance(
            self.effective_to,
            date,
        ):
            raise TypeError(
                "effective_to must be a date"
            )

        if self.effective_from > self.effective_to:
            raise ValueError(
                "effective_from must not be "
                "after effective_to"
            )

        if not isinstance(
            self.status,
            TeacherTimetableSlotStatus,
        ):
            raise TypeError(
                "status must be "
                "TeacherTimetableSlotStatus"
            )

    @property
    def position_key(
        self,
    ) -> tuple[int, TeachingSession, int]:
        return (
            self.weekday,
            self.session,
            self.period,
        )
