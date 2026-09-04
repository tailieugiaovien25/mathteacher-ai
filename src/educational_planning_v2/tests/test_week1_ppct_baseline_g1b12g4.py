from datetime import date
from educational_planning_v2.models.weekly_teaching_schedule import AcademicWeek, CurriculumPeriod, TeachingSession, TimetableSlot
from educational_planning_v2.services.weekly_teaching_schedule_service import WeeklyTeachingScheduleService

def slot(start):
    return TimetableSlot(teacher_id="GV001",class_id="6A1",subject_ref="ENGLISH",component_ref=None,weekday=1,timetable_period=1,session=TeachingSession.MORNING,effective_from=start,effective_to=date(2027,5,31))

def cp(n):
    return CurriculumPeriod(class_id="6A1",subject_ref="ENGLISH",period_number=n,lesson_id="L"+str(n),lesson_title="Lesson "+str(n),period_in_lesson=1,total_lesson_periods=1,component_ref=None,teaching_equipment=())

def test_week1_ignores_tkb_occurrences_before_configured_year_start():
    week=AcademicWeek(academic_year="2026-2027",week_number=1,start_date=date(2026,9,7),end_date=date(2026,9,13))
    r=WeeklyTeachingScheduleService().build(schedule_id="W1",teacher_id="GV001",academic_week=week,timetable_slots=(slot(date(2026,7,27)),),curriculum_periods=tuple(cp(i) for i in range(1,20)),execution_records=())
    assert [x.curriculum_period for x in r.entries] == [1]
    assert r.metadata["completed_execution_count"] == 0
    assert r.metadata["period_baseline_source"] == "ACADEMIC_YEAR_WEEK1"

def test_week2_preserves_existing_timetable_fallback():
    week=AcademicWeek(academic_year="2026-2027",week_number=2,start_date=date(2026,9,14),end_date=date(2026,9,20))
    r=WeeklyTeachingScheduleService().build(schedule_id="W2",teacher_id="GV001",academic_week=week,timetable_slots=(slot(date(2026,9,7)),),curriculum_periods=tuple(cp(i) for i in range(1,20)),execution_records=())
    assert [x.curriculum_period for x in r.entries] == [2]
    assert r.metadata["period_baseline_source"] == "TIMETABLE_FALLBACK"
