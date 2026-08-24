from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class AcademicWeekStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@dataclass(frozen=True)
class AcademicWeekConfiguration:
    academic_week_id: str
    academic_year_id: str
    academic_year: str
    week_number: int
    start_date: date
    end_date: date
    status: AcademicWeekStatus = AcademicWeekStatus.ACTIVE
    is_manual_override: bool = False
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.academic_week_id.strip():
            raise ValueError("academic_week_id must not be empty")

        if not self.academic_year_id.strip():
            raise ValueError("academic_year_id must not be empty")

        if not self.academic_year.strip():
            raise ValueError("academic_year must not be empty")

        if not 1 <= self.week_number <= 40:
            raise ValueError("week_number must be between 1 and 40")

        if self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date")

        if self.note is not None and len(self.note) > 1000:
            raise ValueError("note must not exceed 1000 characters")
