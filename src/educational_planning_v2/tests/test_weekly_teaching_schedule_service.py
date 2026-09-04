from datetime import date

import pytest

from educational_planning_v2 import (
    AcademicWeek,
    CurriculumPeriod,
    LessonExecutionRecord,
    TimetableSlot,
    WeeklyTeachingScheduleService,
)
from educational_planning_v2.models import (
    TeachingSession,
)


WEEK = AcademicWeek(
    academic_year="2026-2027",
    week_number=5,
    start_date=date(2026, 10, 5),
    end_date=date(2026, 10, 11),
)


def _slot(
    *,
    weekday: int,
    timetable_period: int,
    session: TeachingSession = TeachingSession.MORNING,
    component_ref: str = "ALGEBRA",
    teacher_id: str = "GV001",
) -> TimetableSlot:
    return TimetableSlot(
        teacher_id=teacher_id,
        class_id="8A",
        subject_ref="MATH",
        component_ref=component_ref,
        weekday=weekday,
        timetable_period=timetable_period,
        session=session,
        effective_from=date(2026, 9, 1),
        effective_to=date(2026, 12, 31),
    )


def _curriculum(
    period_number: int,
    *,
    component_ref: str = "ALGEBRA",
) -> CurriculumPeriod:
    return CurriculumPeriod(
        class_id="8A",
        subject_ref="MATH",
        component_ref=component_ref,
        period_number=period_number,
        lesson_id=f"LESSON-{component_ref}-{period_number}",
        lesson_title=f"Lesson {period_number}",
        teaching_equipment=("PROJECTOR",),
    )


def _completed(
    period_number: int,
    *,
    component_ref: str = "ALGEBRA",
    status: str = "COMPLETED",
) -> LessonExecutionRecord:
    return LessonExecutionRecord(
        teacher_id="GV001",
        class_id="8A",
        subject_ref="MATH",
        component_ref=component_ref,
        teaching_date=date(2026, 10, 1),
        curriculum_period=period_number,
        status=status,
    )


def test_builds_week_five_from_completed_period_count():
    service = WeeklyTeachingScheduleService()
    schedule = service.build(
        schedule_id="SCHEDULE-GV001-W05",
        teacher_id="GV001",
        academic_week=WEEK,
        timetable_slots=(
            _slot(weekday=1, timetable_period=1),
            _slot(weekday=4, timetable_period=2),
        ),
        curriculum_periods=(_curriculum(9), _curriculum(10)),
        execution_records=tuple(_completed(period) for period in range(1, 9)),
    )

    assert [entry.curriculum_period for entry in schedule.entries] == [9, 10]
    assert [entry.teaching_date for entry in schedule.entries] == [
        date(2026, 10, 5),
        date(2026, 10, 8),
    ]
    assert schedule.metadata["completed_execution_count"] == 8


def test_components_have_independent_period_sequences():
    service = WeeklyTeachingScheduleService()
    schedule = service.build(
        schedule_id="SCHEDULE-GV001-W05",
        teacher_id="GV001",
        academic_week=WEEK,
        timetable_slots=(
            _slot(weekday=1, timetable_period=1, component_ref="ALGEBRA"),
            _slot(weekday=2, timetable_period=1, component_ref="GEOMETRY"),
        ),
        curriculum_periods=(
            _curriculum(9, component_ref="ALGEBRA"),
            _curriculum(5, component_ref="GEOMETRY"),
        ),
        execution_records=(
            *( _completed(period) for period in range(1, 9) ),
            *(
                _completed(period, component_ref="GEOMETRY")
                for period in range(1, 5)
            ),
        ),
    )

    assert [entry.curriculum_period for entry in schedule.entries] == [9, 5]


def test_non_completed_execution_does_not_advance_sequence():
    schedule = WeeklyTeachingScheduleService().build(
        schedule_id="SCHEDULE-GV001-W05",
        teacher_id="GV001",
        academic_week=WEEK,
        timetable_slots=(_slot(weekday=1, timetable_period=1),),
        curriculum_periods=(_curriculum(1),),
        execution_records=(_completed(1, status="CANCELLED"),),
    )

    assert schedule.entries[0].curriculum_period == 1


def test_other_teacher_slots_are_not_included():
    schedule = WeeklyTeachingScheduleService().build(
        schedule_id="SCHEDULE-GV001-W05",
        teacher_id="GV001",
        academic_week=WEEK,
        timetable_slots=(
            _slot(weekday=1, timetable_period=1, teacher_id="GV002"),
        ),
        curriculum_periods=(),
    )

    assert schedule.entries == ()


def test_inactive_timetable_version_is_not_included():
    inactive = TimetableSlot(
        teacher_id="GV001",
        class_id="8A",
        subject_ref="MATH",
        component_ref="ALGEBRA",
        weekday=1,
        timetable_period=1,
        session=TeachingSession.MORNING,
        effective_from=date(2026, 9, 1),
        effective_to=date(2026, 10, 4),
    )
    schedule = WeeklyTeachingScheduleService().build(
        schedule_id="SCHEDULE-GV001-W05",
        teacher_id="GV001",
        academic_week=WEEK,
        timetable_slots=(inactive,),
        curriculum_periods=(),
    )

    assert schedule.entries == ()


def test_missing_curriculum_period_is_reported():
    with pytest.raises(ValueError, match="missing curriculum period"):
        WeeklyTeachingScheduleService().build(
            schedule_id="SCHEDULE-GV001-W05",
            teacher_id="GV001",
            academic_week=WEEK,
            timetable_slots=(_slot(weekday=1, timetable_period=1),),
            curriculum_periods=(),
        )


def test_duplicate_curriculum_period_is_blocked():
    duplicate = _curriculum(1)

    with pytest.raises(ValueError, match="duplicate curriculum period"):
        WeeklyTeachingScheduleService().build(
            schedule_id="SCHEDULE-GV001-W05",
            teacher_id="GV001",
            academic_week=WEEK,
            timetable_slots=(),
            curriculum_periods=(duplicate, duplicate),
        )


def test_same_period_morning_and_afternoon_are_distinct_and_ordered():
    schedule = WeeklyTeachingScheduleService().build(
        schedule_id="SCHEDULE-GV001-W05-SESSIONS",
        teacher_id="GV001",
        academic_week=WEEK,
        timetable_slots=(
            _slot(
                weekday=1,
                timetable_period=1,
                session=TeachingSession.AFTERNOON,
            ),
            _slot(
                weekday=1,
                timetable_period=1,
                session=TeachingSession.MORNING,
            ),
        ),
        curriculum_periods=(
            _curriculum(1),
            _curriculum(2),
        ),
        execution_records=(
            _completed(1, status="CANCELLED"),
        ),
    )

    assert len(schedule.entries) == 2

    assert [
        entry.session
        for entry in schedule.entries
    ] == [
        TeachingSession.MORNING,
        TeachingSession.AFTERNOON,
    ]

    assert [
        entry.timetable_period
        for entry in schedule.entries
    ] == [1, 1]

    assert [
        entry.curriculum_period
        for entry in schedule.entries
    ] == [1, 2]


def test_core_service_contains_no_storage_or_spreadsheet_dependency():
    import inspect

    source = inspect.getsource(WeeklyTeachingScheduleService).lower()

    for forbidden_token in (
        "openpyxl",
        "load_workbook",
        "pandas",
        ".xlsx",
        ".xlsm",
        "worksheet",
        "supabase",
        "google drive",
    ):
        assert forbidden_token not in source
