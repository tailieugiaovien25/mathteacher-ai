from dataclasses import dataclass

from lesson_planning_v2.lesson_plan_teaching_scope import (
    LessonPlanTeachingScope,
)
from lesson_planning_v2.services.weekly_lesson_plan_grouping_service import (
    WeeklyLessonPlanGroupingService,
)


@dataclass(frozen=True)
class ScheduleItem:
    teacher_id: str
    academic_year: str
    week_number: int
    subject_ref: str
    class_id: str
    period_number: int
    lesson_title: str
    component_ref: str | None = None


def item(
    *,
    class_id="CLASS-6A1",
    period_number=1,
    lesson_title="Lesson 1",
    component_ref=None,
):
    return ScheduleItem(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="FOREIGN-LANGUAGE-1",
        class_id=class_id,
        period_number=period_number,
        lesson_title=lesson_title,
        component_ref=component_ref,
    )


def test_three_periods_same_class_form_one_weekly_group():
    service = WeeklyLessonPlanGroupingService()

    result = service.group_for_class(
        items=(
            item(
                period_number=1,
                lesson_title="Lesson 1",
            ),
            item(
                period_number=2,
                lesson_title="Lesson 2",
            ),
            item(
                period_number=3,
                lesson_title="Lesson 3",
            ),
        ),
    )

    assert len(result) == 1

    group = result[0]

    assert group.identity.teacher_id == "GV002"
    assert group.identity.week_number == 8

    assert (
        group.identity.subject_ref
        == "FOREIGN-LANGUAGE-1"
    )

    assert (
        group.identity.teaching_scope.class_id
        == "CLASS-6A1"
    )

    assert len(group.items) == 3

    assert tuple(
        value.period_number
        for value in group.items
    ) == (
        1,
        2,
        3,
    )


def test_different_classes_form_different_groups():
    service = WeeklyLessonPlanGroupingService()

    result = service.group_for_class(
        items=(
            item(
                class_id="CLASS-6A1",
                period_number=1,
            ),
            item(
                class_id="CLASS-6A2",
                period_number=1,
            ),
        ),
    )

    assert len(result) == 2

    scope_refs = {
        group.identity.teaching_scope.scope_ref
        for group in result
    }

    assert scope_refs == {
        "CLASS-6A1",
        "CLASS-6A2",
    }


def test_different_subjects_form_different_groups():
    service = WeeklyLessonPlanGroupingService()

    math = ScheduleItem(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="MATH",
        class_id="CLASS-6A1",
        period_number=1,
        lesson_title="Math lesson",
    )

    english = item(
        period_number=1,
    )

    result = service.group_for_class(
        items=(
            math,
            english,
        ),
    )

    assert len(result) == 2


def test_different_weeks_form_different_groups():
    service = WeeklyLessonPlanGroupingService()

    week_8 = item(
        period_number=1,
    )

    week_9 = ScheduleItem(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=9,
        subject_ref="FOREIGN-LANGUAGE-1",
        class_id="CLASS-6A1",
        period_number=1,
        lesson_title="Lesson next week",
    )

    result = service.group_for_class(
        items=(
            week_8,
            week_9,
        ),
    )

    assert len(result) == 2


def test_different_teachers_form_different_groups():
    service = WeeklyLessonPlanGroupingService()

    teacher_1 = item(
        period_number=1,
    )

    teacher_2 = ScheduleItem(
        teacher_id="GV003",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="FOREIGN-LANGUAGE-1",
        class_id="CLASS-6A1",
        period_number=2,
        lesson_title="Lesson 2",
    )

    result = service.group_for_class(
        items=(
            teacher_1,
            teacher_2,
        ),
    )

    assert len(result) == 2


def test_component_does_not_split_weekly_subject_group():
    service = WeeklyLessonPlanGroupingService()

    result = service.group_for_class(
        items=(
            item(
                period_number=1,
                component_ref="COMPONENT-A",
            ),
            item(
                period_number=2,
                component_ref="COMPONENT-B",
            ),
        ),
    )

    assert len(result) == 1
    assert len(result[0].items) == 2


def test_group_identity_uses_class_scope():
    service = WeeklyLessonPlanGroupingService()

    result = service.group_for_class(
        items=(
            item(),
        ),
    )

    expected_scope = (
        LessonPlanTeachingScope.for_class(
            class_id="CLASS-6A1",
        )
    )

    assert (
        result[0].identity.teaching_scope
        == expected_scope
    )
