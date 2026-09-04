from datetime import date
import pytest
from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroup, LessonPlanGroupingMode, TeachingOccurrence
from lesson_planning_v2.services.canonical_lesson_plan_naming_service import CanonicalLessonPlanNamingError, CanonicalLessonPlanNamingService

def _group(mode=LessonPlanGroupingMode.BY_WEEK, week=1):
    return LessonPlanGroup(
        group_id="lpg_test", grouping_mode=mode, subject_ref="A", component_ref="", grade=8,
        lesson_id=None, lesson_title="Unit", curriculum_periods=(6,3,5,4),
        occurrences=(TeachingOccurrence(row_index=0,class_id="8A1",teaching_date=date(2026,9,7),timetable_period=1,timetable_slot_id=None,curriculum_period=3),),
        representative_row_index=0, academic_year="2026-2027", week_number=week,
    )

def test_week_name():
    assert CanonicalLessonPlanNamingService().expected_name(_group()).filename == "8GA003W01.docx"

def test_period_name():
    assert CanonicalLessonPlanNamingService().expected_name(_group(LessonPlanGroupingMode.BY_PERIOD)).filename == "8GA003.docx"

def test_upload_exact_name():
    s=CanonicalLessonPlanNamingService()
    s.validate_upload_filename(_group(), r"C:\tmp\8ga003w01.DOCX")
    with pytest.raises(CanonicalLessonPlanNamingError):
        s.validate_upload_filename(_group(), "8GA004W01.docx")

def test_week_required():
    with pytest.raises(CanonicalLessonPlanNamingError):
        CanonicalLessonPlanNamingService().expected_name(_group(week=None))
