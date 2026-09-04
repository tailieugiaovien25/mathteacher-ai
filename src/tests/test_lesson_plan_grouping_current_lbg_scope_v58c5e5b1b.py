from types import SimpleNamespace
import pytest

from lesson_planning_v2.services.lesson_plan_grouping_service import (
    LessonPlanGroupValidationError,
    LessonPlanGroupingMode,
    LessonPlanGroupingPolicyResolver,
    LessonPlanGroupingService,
)


def make_row(*, week=1, lesson_id="L3", lesson_group_id=""):
    return SimpleNamespace(
        academic_year="2026-2027",
        week_number=week,
        subject_ref="A",
        component_ref="",
        grade=8,
        curriculum_period=3,
        lesson_id=lesson_id,
        lesson_group_id=lesson_group_id,
        lesson_title="Mutable title",
        class_id="8A1",
        teaching_date=None,
        timetable_period=1,
        timetable_slot_id="slot-1",
    )


@pytest.mark.parametrize(
    "mode",
    [
        LessonPlanGroupingMode.BY_PERIOD,
        LessonPlanGroupingMode.BY_LESSON,
    ],
)
def test_same_business_identity_never_merges_across_week(mode):
    resolver = LessonPlanGroupingPolicyResolver(default_mode=mode)
    groups = LessonPlanGroupingService().group(
        [make_row(week=1), make_row(week=2)],
        policy_resolver=resolver,
    )
    assert len(groups) == 2


def test_by_lesson_uses_stable_lesson_group_id_when_lesson_id_missing():
    resolver = LessonPlanGroupingPolicyResolver(
        default_mode=LessonPlanGroupingMode.BY_LESSON
    )
    groups = LessonPlanGroupingService().group(
        [make_row(lesson_id="", lesson_group_id="LG-3")],
        policy_resolver=resolver,
    )
    assert len(groups) == 1


def test_by_lesson_rejects_mutable_title_as_identity():
    resolver = LessonPlanGroupingPolicyResolver(
        default_mode=LessonPlanGroupingMode.BY_LESSON
    )
    with pytest.raises(
        LessonPlanGroupValidationError,
        match="BY_LESSON_REQUIRES_STABLE_LESSON_ID",
    ):
        LessonPlanGroupingService().group(
            [make_row(lesson_id="", lesson_group_id="")],
            policy_resolver=resolver,
        )
