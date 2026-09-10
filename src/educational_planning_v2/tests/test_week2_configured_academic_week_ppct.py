from datetime import date

from educational_planning_v2.models.teacher_timetable import TeachingSession
from educational_planning_v2.models.weekly_teaching_schedule import (
    AcademicWeek,
    CurriculumPeriod,
    TimetableSlot,
)
from educational_planning_v2.services.weekly_teaching_schedule_service import (
    WeeklyTeachingScheduleService,
)


def _slot(*, class_id: str, weekday: int, period: int) -> TimetableSlot:
    return TimetableSlot(
        teacher_id="GV001",
        class_id=class_id,
        subject_ref="ENGLISH",
        component_ref=None,
        weekday=weekday,
        timetable_period=period,
        session=TeachingSession.MORNING,
        effective_from=date(2026, 7, 27),
        effective_to=date(2027, 5, 31),
    )


def _curriculum(class_id: str) -> tuple[CurriculumPeriod, ...]:
    return tuple(
        CurriculumPeriod(
            class_id=class_id,
            subject_ref="ENGLISH",
            component_ref=None,
            period_number=number,
            lesson_id=f"{class_id}-{number}",
            lesson_title=f"Lesson {number}",
        )
        for number in range(1, 20)
    )


def test_week2_counts_only_configured_week1_not_pre_school_dates():
    week1 = AcademicWeek(
        "2026-2027", 1, date(2026, 9, 7), date(2026, 9, 13)
    )
    week2 = AcademicWeek(
        "2026-2027", 2, date(2026, 9, 14), date(2026, 9, 20)
    )
    slots = (
        _slot(class_id="7A1", weekday=1, period=2),
        _slot(class_id="7A1", weekday=3, period=2),
        _slot(class_id="9A2", weekday=2, period=1),
    )

    schedule = WeeklyTeachingScheduleService().build(
        schedule_id="W2",
        teacher_id="GV001",
        academic_week=week2,
        timetable_slots=slots,
        curriculum_periods=(
            *_curriculum("7A1"),
            *_curriculum("9A2"),
        ),
        execution_records=(),
        prior_academic_weeks=(week1,),
    )

    periods_by_class = {}
    for entry in schedule.entries:
        periods_by_class.setdefault(entry.class_id, []).append(
            entry.curriculum_period
        )

    assert periods_by_class == {
        "7A1": [3, 4],
        "9A2": [2],
    }
    assert (
        schedule.metadata["period_baseline_source"]
        == "CONFIGURED_ACADEMIC_WEEKS"
    )
    assert schedule.metadata["completed_execution_count"] == 3


def test_configured_week_gap_does_not_create_phantom_periods():
    week1 = AcademicWeek(
        "2026-2027", 1, date(2026, 9, 7), date(2026, 9, 13)
    )
    week3 = AcademicWeek(
        "2026-2027", 3, date(2026, 9, 28), date(2026, 10, 4)
    )
    slot = _slot(class_id="7A1", weekday=1, period=2)

    schedule = WeeklyTeachingScheduleService().build(
        schedule_id="W3",
        teacher_id="GV001",
        academic_week=week3,
        timetable_slots=(slot,),
        curriculum_periods=_curriculum("7A1"),
        execution_records=(),
        prior_academic_weeks=(week1,),
    )

    assert [entry.curriculum_period for entry in schedule.entries] == [2]
