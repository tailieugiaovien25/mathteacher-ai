"""Supabase implementation of the weekly-schedule repository port."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from educational_planning_v2.adapters.weekly_schedule_codec import schedule_from_dict, schedule_to_dict
from educational_planning_v2.models import WeeklyTeachingSchedule
from educational_planning_v2.repositories import SavedWeeklyScheduleSummary


class SupabaseWeeklyScheduleRepository:
    """Persist schedules under the authenticated teacher account."""

    def __init__(self, client: Any, user_id: str, table_name: str = "weekly_teaching_schedules") -> None:
        self._client = client
        self._user_id = self._required_text(user_id, "user_id")
        self._table_name = self._required_text(table_name, "table_name")

    def save(self, schedule: WeeklyTeachingSchedule) -> SavedWeeklyScheduleSummary:
        if not isinstance(schedule, WeeklyTeachingSchedule):
            raise TypeError("schedule must be a WeeklyTeachingSchedule")
        now = datetime.now(timezone.utc)
        row = {
            "user_id": self._user_id, "schedule_id": schedule.schedule_id,
            "teacher_id": schedule.teacher_id, "academic_year": schedule.academic_week.academic_year,
            "week_number": schedule.academic_week.week_number, "entry_count": len(schedule.entries),
            "schedule_data": schedule_to_dict(schedule), "updated_at": now.isoformat(),
        }
        response = self._client.table(self._table_name).upsert(
            row, on_conflict="user_id,schedule_id"
        ).execute()
        rows = self._response_rows(response)
        saved_at = self._parse_datetime(rows[0].get("updated_at")) if rows else now
        return self._summary(schedule, saved_at)

    def get(self, schedule_id: str) -> WeeklyTeachingSchedule | None:
        normalized = self._required_text(schedule_id, "schedule_id")
        response = (
            self._client.table(self._table_name).select("schedule_data")
            .eq("user_id", self._user_id).eq("schedule_id", normalized).limit(1).execute()
        )
        rows = self._response_rows(response)
        return schedule_from_dict(rows[0]["schedule_data"]) if rows else None

    def list_for_teacher(self, teacher_id: str) -> tuple[SavedWeeklyScheduleSummary, ...]:
        normalized = self._required_text(teacher_id, "teacher_id")
        response = (
            self._client.table(self._table_name)
            .select("schedule_id,teacher_id,academic_year,week_number,entry_count,updated_at")
            .eq("user_id", self._user_id).eq("teacher_id", normalized)
            .order("updated_at", desc=True).execute()
        )
        return tuple(SavedWeeklyScheduleSummary(
            schedule_id=row["schedule_id"], teacher_id=row["teacher_id"],
            academic_year=row["academic_year"], week_number=row["week_number"],
            entry_count=row["entry_count"], updated_at=self._parse_datetime(row["updated_at"]),
        ) for row in self._response_rows(response))

    @staticmethod
    def _response_rows(response: Any) -> list[dict[str, Any]]:
        rows = getattr(response, "data", None)
        if rows is None:
            raise ValueError("Supabase response does not contain data")
        if not isinstance(rows, list):
            raise TypeError("Supabase response data must be a list")
        return rows

    @staticmethod
    def _parse_datetime(value: str | datetime) -> datetime:
        return value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _required_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} must not be empty")
        return normalized

    @staticmethod
    def _summary(schedule: WeeklyTeachingSchedule, updated_at: datetime) -> SavedWeeklyScheduleSummary:
        return SavedWeeklyScheduleSummary(
            schedule.schedule_id, schedule.teacher_id, schedule.academic_week.academic_year,
            schedule.academic_week.week_number, len(schedule.entries), updated_at,
        )
