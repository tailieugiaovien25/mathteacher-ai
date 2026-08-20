"""Canonical JSON-compatible representation of a weekly schedule."""

from __future__ import annotations

from datetime import date
from typing import Any

from educational_planning_v2.models import AcademicWeek, TeachingSession, WeeklyTeachingSchedule, WeeklyTeachingScheduleEntry


def schedule_to_dict(schedule: WeeklyTeachingSchedule) -> dict[str, Any]:
    if not isinstance(schedule, WeeklyTeachingSchedule):
        raise TypeError("schedule must be a WeeklyTeachingSchedule")
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


def schedule_from_dict(data: dict[str, Any]) -> WeeklyTeachingSchedule:
    if not isinstance(data, dict):
        raise TypeError("schedule data must be a dict")
    week = data["academic_week"]
    return WeeklyTeachingSchedule(
        schedule_id=data["schedule_id"], teacher_id=data["teacher_id"],
        academic_week=AcademicWeek(
            academic_year=week["academic_year"], week_number=week["week_number"],
            start_date=date.fromisoformat(week["start_date"]), end_date=date.fromisoformat(week["end_date"]),
        ),
        entries=tuple(WeeklyTeachingScheduleEntry(
            teaching_date=date.fromisoformat(item["teaching_date"]), weekday=item["weekday"],
            timetable_period=item["timetable_period"], session=TeachingSession(item.get("session", "MORNING")), teacher_id=item["teacher_id"],
            class_id=item["class_id"], subject_ref=item["subject_ref"], component_ref=item.get("component_ref"),
            curriculum_period=item["curriculum_period"], lesson_id=item["lesson_id"], lesson_title=item["lesson_title"],
            period_in_lesson=item["period_in_lesson"], total_lesson_periods=item["total_lesson_periods"],
            teaching_equipment=tuple(item.get("teaching_equipment", ())),
        ) for item in data["entries"]), metadata=dict(data.get("metadata", {})),
    )
