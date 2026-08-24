from datetime import date

from educational_planning_v2.models.teacher_timetable import (
    TeachingSession,
)
from educational_planning_v2.models.weekly_teaching_schedule import (
    AcademicWeek,
    CurriculumPeriod,
    TimetableSlot,
)
from educational_planning_v2.services.weekly_teaching_schedule_service import (
    WeeklyTeachingScheduleService,
)


def _slot(session: TeachingSession) -> TimetableSlot:
    return TimetableSlot(
        teacher_id="teacher-1",
        class_id="6A1",
        subject_ref="math",
        component_ref="number",
        weekday=1,
        timetable_period=2,
        session=session,
        effective_from=date(2026, 9, 7),
        effective_to=date(2027, 5, 31),
    )


def test_week_four_uses_prior_timetable_and_deduplicates_exact_slot():
    slots = (
        _slot(TeachingSession.MORNING),
        _slot(TeachingSession.MORNING),
        _slot(TeachingSession.AFTERNOON),
    )
    curriculum = tuple(
        CurriculumPeriod(
            class_id="6A1",
            subject_ref="math",
            component_ref="number",
            period_number=period,
            lesson_id=f"lesson-{period}",
            lesson_title=f"Lesson {period}",
        )
        for period in range(1, 30)
    )

    schedule = WeeklyTeachingScheduleService().build(
        schedule_id="week-4",
        teacher_id="teacher-1",
        academic_week=AcademicWeek(
            academic_year="2026-2027",
            week_number=4,
            start_date=date(2026, 9, 28),
            end_date=date(2026, 10, 4),
        ),
        timetable_slots=slots,
        curriculum_periods=curriculum,
    )

    assert len(schedule.entries) == 2
    assert tuple(
        entry.session
        for entry in schedule.entries
    ) == (
        TeachingSession.MORNING,
        TeachingSession.AFTERNOON,
    )
    assert tuple(
        entry.curriculum_period
        for entry in schedule.entries
    ) == (7, 8)
    assert schedule.metadata[
        "duplicate_timetable_slot_count"
    ] == 1
    assert schedule.metadata[
        "period_baseline_source"
    ] == "TIMETABLE_FALLBACK"


def test_explicit_execution_history_remains_authoritative():
    from educational_planning_v2.models.weekly_teaching_schedule import (
        LessonExecutionRecord,
    )

    history = tuple(
        LessonExecutionRecord(
            teacher_id="teacher-1",
            class_id="6A1",
            subject_ref="math",
            component_ref="number",
            teaching_date=date(2026, 9, 1),
            curriculum_period=period,
            status="COMPLETED",
        )
        for period in range(1, 5)
    )
    curriculum = tuple(
        CurriculumPeriod(
            class_id="6A1",
            subject_ref="math",
            component_ref="number",
            period_number=period,
            lesson_id=f"lesson-{period}",
            lesson_title=f"Lesson {period}",
        )
        for period in range(1, 20)
    )

    schedule = WeeklyTeachingScheduleService().build(
        schedule_id="explicit-history",
        teacher_id="teacher-1",
        academic_week=AcademicWeek(
            academic_year="2026-2027",
            week_number=4,
            start_date=date(2026, 9, 28),
            end_date=date(2026, 10, 4),
        ),
        timetable_slots=(_slot(TeachingSession.MORNING),),
        curriculum_periods=curriculum,
        execution_records=history,
    )

    assert schedule.entries[0].curriculum_period == 5
    assert schedule.metadata[
        "period_baseline_source"
    ] == "EXECUTION_RECORDS"
