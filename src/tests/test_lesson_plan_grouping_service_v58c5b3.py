from types import SimpleNamespace

import pytest

from lesson_planning_v2.models.lesson_plan_grouping import (
    LessonPlanGroupValidationError,
    LessonPlanGroupingMode,
)
from lesson_planning_v2.services.lesson_plan_grouping_service import (
    LessonPlanGroupingPolicyResolver,
    LessonPlanGroupingService,
)


def row(**overrides):
    data = dict(
        subject_ref="ENG",
        component_ref="",
        grade=8,
        curriculum_period=10,
        lesson_id="L1",
        lesson_title="Unit 2",
        class_id="8A1",
        teaching_date="2026-09-08",
        timetable_period=2,
        timetable_slot_id="slot-1",
    )
    data.update(overrides)
    return SimpleNamespace(
        academic_year="2026-2027",
        week_number=1,**data)


def resolver(mode=LessonPlanGroupingMode.BY_PERIOD):
    return LessonPlanGroupingPolicyResolver.from_mapping(
        {("ENG", ""): mode}
    )


def test_missing_canonical_grade_fails_closed():
    with pytest.raises(LessonPlanGroupValidationError):
        LessonPlanGroupingService().group(
            (row(grade=None),),
            policy_resolver=resolver(),
        )


def test_period_group_never_mixes_grades():
    groups = LessonPlanGroupingService().group(
        (
            row(grade=6, class_id="6A1"),
            row(grade=8, class_id="8A1"),
        ),
        policy_resolver=resolver(),
    )
    assert len(groups) == 2
    assert [g.grade for g in groups] == [6, 8]


def test_lesson_group_never_mixes_grades():
    groups = LessonPlanGroupingService().group(
        (
            row(grade=6, class_id="6A1"),
            row(grade=8, class_id="8A1"),
        ),
        policy_resolver=resolver(LessonPlanGroupingMode.BY_LESSON),
    )
    assert len(groups) == 2
    assert {g.grade for g in groups} == {6, 8}


def test_canonical_grade_resolver_can_supply_grade():
    groups = LessonPlanGroupingService().group(
        (
            row(grade=None, class_id="8A1"),
            row(grade=None, class_id="8A2"),
        ),
        policy_resolver=resolver(),
        grade_resolver=lambda item: 8,
    )
    assert len(groups) == 1
    assert groups[0].grade == 8
    assert groups[0].class_ids == ("8A1", "8A2")
