"""Local JSON implementation of the weekly-schedule repository port."""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from educational_planning_v2.models import AcademicWeek, TeachingSession, WeeklyTeachingSchedule, WeeklyTeachingScheduleEntry
from educational_planning_v2.repositories import SavedWeeklyScheduleSummary


class LocalWeeklyScheduleRepository:
    """Persist one canonical schedule per safe schedule id."""

    _SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,199}$")

    def __init__(self, storage_root: str | Path) -> None:
        self._root = Path(storage_root)

    def save(self, schedule: WeeklyTeachingSchedule) -> SavedWeeklyScheduleSummary:
        if not isinstance(schedule, WeeklyTeachingSchedule):
            raise TypeError("schedule must be a WeeklyTeachingSchedule")
        target = self._path(schedule.schedule_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        updated_at = datetime.now(timezone.utc)
        payload = {"schema_version": 1, "updated_at": updated_at.isoformat(), "schedule": self._schedule_to_dict(schedule)}
        fd, temporary_name = tempfile.mkstemp(prefix=f".{target.stem}-", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_name, target)
        except Exception:
            Path(temporary_name).unlink(missing_ok=True)
            raise
        return self._summary(schedule, updated_at)

    def get(self, schedule_id: str) -> WeeklyTeachingSchedule | None:
        path = self._path(schedule_id)
        if not path.exists():
            return None
        return self._schedule_from_dict(self._read_payload(path)["schedule"])

    def list_for_teacher(self, teacher_id: str) -> tuple[SavedWeeklyScheduleSummary, ...]:
        normalized = self._required_text(teacher_id, "teacher_id")
        summaries = []
        if not self._root.exists():
            return ()
        for path in self._root.glob("*.json"):
            payload = self._read_payload(path)
            schedule = self._schedule_from_dict(payload["schedule"])
            if schedule.teacher_id == normalized:
                summaries.append(self._summary(schedule, datetime.fromisoformat(payload["updated_at"])))
        return tuple(sorted(summaries, key=lambda item: (item.academic_year, item.week_number, item.updated_at), reverse=True))

    def _path(self, schedule_id: str) -> Path:
        normalized = self._required_text(schedule_id, "schedule_id")
        if not self._SAFE_ID.fullmatch(normalized):
            raise ValueError("schedule_id contains unsafe characters")
        return self._root / f"{normalized}.json"

    @staticmethod
    def _required_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} must not be empty")
        return normalized

    @staticmethod
    def _read_payload(path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Cannot read saved schedule {path.name}: {error}") from error
        if payload.get("schema_version") != 1:
            raise ValueError(f"Unsupported saved schedule schema in {path.name}")
        return payload

    @staticmethod
    def _summary(schedule: WeeklyTeachingSchedule, updated_at: datetime) -> SavedWeeklyScheduleSummary:
        return SavedWeeklyScheduleSummary(schedule.schedule_id, schedule.teacher_id, schedule.academic_week.academic_year, schedule.academic_week.week_number, len(schedule.entries), updated_at)

    @staticmethod
    def _schedule_to_dict(schedule: WeeklyTeachingSchedule) -> dict[str, Any]:
        return {
            "schedule_id": schedule.schedule_id,
            "teacher_id": schedule.teacher_id,
            "academic_week": {
                "academic_year": schedule.academic_week.academic_year,
                "week_number": schedule.academic_week.week_number,
                "start_date": schedule.academic_week.start_date.isoformat(),
                "end_date": schedule.academic_week.end_date.isoformat(),
            },
            "entries": [{
                "teaching_date": item.teaching_date.isoformat(), "weekday": item.weekday,
                "timetable_period": item.timetable_period, "session": item.session.value, "teacher_id": item.teacher_id,
                "class_id": item.class_id, "subject_ref": item.subject_ref,
                "component_ref": item.component_ref, "curriculum_period": item.curriculum_period,
                "lesson_id": item.lesson_id, "lesson_title": item.lesson_title,
                "period_in_lesson": item.period_in_lesson, "total_lesson_periods": item.total_lesson_periods,
                "teaching_equipment": list(item.teaching_equipment),
            } for item in schedule.entries],
            "metadata": schedule.metadata,
        }

    @staticmethod
    def _schedule_from_dict(data: dict[str, Any]) -> WeeklyTeachingSchedule:
        week = data["academic_week"]
        return WeeklyTeachingSchedule(
            schedule_id=data["schedule_id"], teacher_id=data["teacher_id"],
            academic_week=AcademicWeek(week["academic_year"], week["week_number"], date.fromisoformat(week["start_date"]), date.fromisoformat(week["end_date"])),
            entries=tuple(WeeklyTeachingScheduleEntry(
                teaching_date=date.fromisoformat(item["teaching_date"]), weekday=item["weekday"],
                timetable_period=item["timetable_period"], session=TeachingSession(item.get("session", "MORNING")), teacher_id=item["teacher_id"],
                class_id=item["class_id"], subject_ref=item["subject_ref"],
                component_ref=item.get("component_ref"), curriculum_period=item["curriculum_period"],
                lesson_id=item["lesson_id"], lesson_title=item["lesson_title"],
                period_in_lesson=item["period_in_lesson"], total_lesson_periods=item["total_lesson_periods"],
                teaching_equipment=tuple(item.get("teaching_equipment", ())),
            ) for item in data["entries"]), metadata=dict(data.get("metadata", {})),
        )
