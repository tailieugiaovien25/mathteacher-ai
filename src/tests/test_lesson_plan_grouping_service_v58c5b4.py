from types import SimpleNamespace
import pytest
from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroupValidationError, LessonPlanGroupingMode
from lesson_planning_v2.services.lesson_plan_grouping_service import LessonPlanGroupingPolicyResolver, LessonPlanGroupingService

def r(**kw):
    data=dict(academic_year="2026-2027",week_number=3,subject_ref="ENG",component_ref="",grade=8,curriculum_period=9,lesson_id="U2",lesson_title="Unit 2",class_id="8A1",teaching_date="2026-09-14",timetable_period=1,timetable_slot_id="s1")
    data.update(kw)
    return SimpleNamespace(**data)

def resolver():
    return LessonPlanGroupingPolicyResolver.from_mapping({("ENG",""):LessonPlanGroupingMode.BY_WEEK})

def test_by_week_groups_multiple_periods_and_classes():
    groups=LessonPlanGroupingService().group((r(),r(curriculum_period=10,class_id="8A2",timetable_slot_id="s2"),r(curriculum_period=11,timetable_slot_id="s3")),policy_resolver=resolver())
    assert len(groups)==1
    assert groups[0].grade==8
    assert groups[0].curriculum_periods==(9,10,11)
    assert groups[0].class_ids==("8A1","8A2")

def test_by_week_never_crosses_grade():
    assert len(LessonPlanGroupingService().group((r(grade=8),r(grade=9,class_id="9A1")),policy_resolver=resolver()))==2

def test_by_week_never_crosses_week():
    assert len(LessonPlanGroupingService().group((r(week_number=3),r(week_number=4)),policy_resolver=resolver()))==2

def test_by_week_never_crosses_academic_year():
    assert len(LessonPlanGroupingService().group((r(),r(academic_year="2027-2028")),policy_resolver=resolver()))==2

def test_by_week_requires_week():
    with pytest.raises(LessonPlanGroupValidationError,match="BY_WEEK_REQUIRES_ACADEMIC_YEAR_AND_WEEK"):
        LessonPlanGroupingService().group((r(week_number=None),),policy_resolver=resolver())

def test_by_week_requires_academic_year():
    with pytest.raises(LessonPlanGroupValidationError,match="BY_WEEK_REQUIRES_ACADEMIC_YEAR_AND_WEEK"):
        LessonPlanGroupingService().group((r(academic_year=""),),policy_resolver=resolver())
