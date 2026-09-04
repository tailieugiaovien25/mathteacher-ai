from types import SimpleNamespace

from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroupingMode
from lesson_planning_v2.services.lesson_plan_grouping_service import (
    LessonPlanGroupingPolicyResolver,
    LessonPlanGroupingService,
)


def row(**overrides):
    data = dict(
        subject_ref="ENG",
        component_ref="",
        grade=8,
        academic_year="2026-2027",
        week_number=1,
        curriculum_period=10,
        lesson_id="L1",
        lesson_title="Unit 2",
        class_id="8A1",
        teaching_date="2026-09-08",
        timetable_period=2,
        timetable_slot_id="slot-1",
    )
    data.update(overrides)
    return SimpleNamespace(**data)


def test_by_period_groups_same_ppct_across_classes():
    resolver = LessonPlanGroupingPolicyResolver.from_mapping(
        {("ENG", ""): LessonPlanGroupingMode.BY_PERIOD}
    )
    groups = LessonPlanGroupingService().group(
        (
            row(class_id="8A1", timetable_period=2),
            row(class_id="8A2", timetable_period=4),
        ),
        policy_resolver=resolver,
    )
    assert len(groups) == 1
    assert groups[0].class_ids == ("8A1", "8A2")
    assert groups[0].curriculum_periods == (10,)


def test_by_period_separates_different_ppct():
    resolver = LessonPlanGroupingPolicyResolver.from_mapping(
        {("ENG", ""): "BY_PERIOD"}
    )
    groups = LessonPlanGroupingService().group(
        (
            row(curriculum_period=10),
            row(curriculum_period=11),
        ),
        policy_resolver=resolver,
    )
    assert len(groups) == 2


def test_by_lesson_groups_multiple_ppct_and_classes():
    resolver = LessonPlanGroupingPolicyResolver.from_mapping(
        {("MATH", "ALG"): LessonPlanGroupingMode.BY_LESSON}
    )
    groups = LessonPlanGroupingService().group(
        (
            row(subject_ref="MATH", component_ref="ALG", curriculum_period=20, lesson_id="ALG-L5", lesson_title="B?i 5", class_id="8A1"),
            row(subject_ref="MATH", component_ref="ALG", curriculum_period=21, lesson_id="ALG-L5", lesson_title="B?i 5", class_id="8A1"),
            row(subject_ref="MATH", component_ref="ALG", curriculum_period=20, lesson_id="ALG-L5", lesson_title="B?i 5", class_id="8A2"),
        ),
        policy_resolver=resolver,
    )
    assert len(groups) == 1
    assert groups[0].curriculum_periods == (20, 21)
    assert groups[0].class_ids == ("8A1", "8A2")
    assert len(groups[0].occurrences) == 3


def test_subject_default_policy_applies_to_components():
    resolver = LessonPlanGroupingPolicyResolver.from_mapping(
        {("MATH", ""): LessonPlanGroupingMode.BY_LESSON}
    )
    assert resolver.resolve(
        subject_ref="MATH",
        component_ref="ALG",
    ) is LessonPlanGroupingMode.BY_LESSON


def test_default_policy_is_by_period():
    resolver = LessonPlanGroupingPolicyResolver()
    assert resolver.resolve(
        subject_ref="UNKNOWN",
        component_ref="",
    ) is LessonPlanGroupingMode.BY_PERIOD


def test_occurrence_keeps_class_date_timetable_together():
    resolver = LessonPlanGroupingPolicyResolver.from_mapping(
        {("ENG", ""): LessonPlanGroupingMode.BY_PERIOD}
    )
    group = LessonPlanGroupingService().group(
        (
            row(class_id="8A1", teaching_date="2026-09-08", timetable_period=2),
            row(class_id="8A2", teaching_date="2026-09-09", timetable_period=4),
        ),
        policy_resolver=resolver,
    )[0]
    assert [
        (item.class_id, item.teaching_date, item.timetable_period)
        for item in group.occurrences
    ] == [
        ("8A1", "2026-09-08", 2),
        ("8A2", "2026-09-09", 4),
    ]
