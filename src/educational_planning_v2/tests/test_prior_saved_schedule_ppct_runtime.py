from datetime import date

import pytest

from educational_planning_v2.models.teacher_timetable import TeachingSession
from educational_planning_v2.models.weekly_teaching_schedule import (
    AcademicWeek,
    CurriculumPeriod,
    LessonExecutionRecord,
    TimetableSlot,
    WeeklyTeachingSchedule,
    WeeklyTeachingScheduleEntry,
)
from educational_planning_v2.services.weekly_teaching_schedule_service import (
    WeeklyTeachingScheduleService,
)
from portal_v2.runtime import system_weekly_schedule_runtime as runtime_module
from portal_v2.runtime.system_weekly_schedule_runtime import (
    SystemWeeklyScheduleRuntime,
)


def _week(number: int, start_day: int) -> AcademicWeek:
    return AcademicWeek(
        academic_year="2026-2027",
        week_number=number,
        start_date=date(2026, 9, start_day),
        end_date=date(2026, 9, start_day + 6),
    )


def _schedule(week: AcademicWeek, periods_by_class: dict[str, tuple[int, ...]]):
    entries = []
    for class_id, periods in periods_by_class.items():
        for offset, curriculum_period in enumerate(periods):
            entries.append(
                WeeklyTeachingScheduleEntry(
                    teaching_date=week.start_date,
                    weekday=1,
                    timetable_period=offset + 1,
                    session=TeachingSession.MORNING,
                    teacher_id="teacher-1",
                    class_id=class_id,
                    subject_ref="ENGLISH",
                    component_ref=None,
                    curriculum_period=curriculum_period,
                    lesson_id=f"{class_id}-{curriculum_period}",
                    lesson_title=f"Lesson {curriculum_period}",
                )
            )
    return WeeklyTeachingSchedule(
        schedule_id=(
            f"SYSTEM-teacher-1-2026-2027-W{week.week_number}"
        ),
        teacher_id="teacher-1",
        academic_week=week,
        entries=tuple(entries),
    )


def _runtime(monkeypatch, schedules):
    class Repository:
        def __init__(self, client, user_id):
            assert client == "client"
            assert user_id == "teacher-1"

        def get(self, schedule_id):
            return schedules.get(schedule_id)

    monkeypatch.setattr(
        runtime_module,
        "SupabaseWeeklyScheduleRepository",
        Repository,
    )
    runtime = object.__new__(SystemWeeklyScheduleRuntime)
    runtime._client = "client"
    runtime._user_id = "teacher-1"
    return runtime


def test_week3_uses_each_class_rows_from_saved_weeks(monkeypatch):
    week1 = _week(1, 7)
    week2 = _week(2, 14)
    week3 = _week(3, 21)
    schedules = {
        "SYSTEM-teacher-1-2026-2027-W1": _schedule(
            week1, {"6A1": (1, 2), "7A1": (1,)}
        ),
        "SYSTEM-teacher-1-2026-2027-W2": _schedule(
            week2, {"6A1": (3,), "7A1": (2, 3)}
        ),
    }
    runtime = _runtime(monkeypatch, schedules)

    records = runtime._load_prior_schedule_records(
        academic_year="2026-2027",
        current_week=week3,
        prior_academic_weeks=(week1, week2),
    )

    assert sum(record.class_id == "6A1" for record in records) == 3
    assert sum(record.class_id == "7A1" for record in records) == 3


def test_missing_prior_week_fails_closed(monkeypatch):
    week1 = _week(1, 7)
    week2 = _week(2, 14)
    runtime = _runtime(monkeypatch, {})

    with pytest.raises(LookupError, match="Tuần 1"):
        runtime._load_prior_schedule_records(
            academic_year="2026-2027",
            current_week=week2,
            prior_academic_weeks=(week1,),
        )


def test_timetable_change_affects_current_week_not_saved_history():
    week3 = _week(3, 21)
    history = (
        LessonExecutionRecord(
            teacher_id="teacher-1",
            class_id="6A1",
            subject_ref="ENGLISH",
            component_ref=None,
            teaching_date=date(2026, 9, 7),
            curriculum_period=1,
            status="COMPLETED",
        ),
        LessonExecutionRecord(
            teacher_id="teacher-1",
            class_id="6A1",
            subject_ref="ENGLISH",
            component_ref=None,
            teaching_date=date(2026, 9, 14),
            curriculum_period=2,
            status="COMPLETED",
        ),
        LessonExecutionRecord(
            teacher_id="teacher-1",
            class_id="7A1",
            subject_ref="ENGLISH",
            component_ref=None,
            teaching_date=date(2026, 9, 7),
            curriculum_period=1,
            status="COMPLETED",
        ),
    )
    current_slots = (
        TimetableSlot(
            teacher_id="teacher-1",
            class_id="6A1",
            subject_ref="ENGLISH",
            component_ref=None,
            weekday=1,
            timetable_period=1,
            session=TeachingSession.MORNING,
            effective_from=week3.start_date,
            effective_to=date(2027, 5, 31),
        ),
        TimetableSlot(
            teacher_id="teacher-1",
            class_id="7A1",
            subject_ref="ENGLISH",
            component_ref=None,
            weekday=2,
            timetable_period=1,
            session=TeachingSession.MORNING,
            effective_from=week3.start_date,
            effective_to=date(2027, 5, 31),
        ),
        TimetableSlot(
            teacher_id="teacher-1",
            class_id="7A1",
            subject_ref="ENGLISH",
            component_ref=None,
            weekday=4,
            timetable_period=2,
            session=TeachingSession.MORNING,
            effective_from=week3.start_date,
            effective_to=date(2027, 5, 31),
        ),
    )
    curriculum = tuple(
        CurriculumPeriod(
            class_id=class_id,
            subject_ref="ENGLISH",
            component_ref=None,
            period_number=number,
            lesson_id=f"{class_id}-{number}",
            lesson_title=f"Lesson {number}",
        )
        for class_id in ("6A1", "7A1")
        for number in range(1, 10)
    )

    schedule = WeeklyTeachingScheduleService().build(
        schedule_id="SYSTEM-teacher-1-2026-2027-W3",
        teacher_id="teacher-1",
        academic_week=week3,
        timetable_slots=current_slots,
        curriculum_periods=curriculum,
        execution_records=history,
    )

    periods_by_class = {}
    for entry in schedule.entries:
        periods_by_class.setdefault(entry.class_id, []).append(
            entry.curriculum_period
        )

    assert periods_by_class == {
        "6A1": [3],
        "7A1": [2, 3],
    }
