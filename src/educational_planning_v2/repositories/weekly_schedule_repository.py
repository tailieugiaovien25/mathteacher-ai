"""Storage-independent contract for saved weekly teaching schedules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from educational_planning_v2.models import WeeklyTeachingSchedule


@dataclass(frozen=True)
class SavedWeeklyScheduleSummary:
    schedule_id: str
    teacher_id: str
    academic_year: str
    week_number: int
    entry_count: int
    updated_at: datetime


class WeeklyScheduleRepository(Protocol):
    """Port implemented by local storage now and Supabase later."""

    def save(self, schedule: WeeklyTeachingSchedule) -> SavedWeeklyScheduleSummary: ...

    def get(self, schedule_id: str) -> WeeklyTeachingSchedule | None: ...

    def list_for_teacher(self, teacher_id: str) -> tuple[SavedWeeklyScheduleSummary, ...]: ...
