from dataclasses import dataclass

import pytest

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
    grade_key: str
    period_number: int
    lesson_title: str
    component_ref: str | None = None


def item(
    *,
    class_id="CLASS-6A1",
    grade_key="GRADE-6",
    period_number=1,
    subject_ref="FOREIGN-LANGUAGE-1",
    teacher_id="GV002",
    week_number=8,
    component_ref=None,
):
    return ScheduleItem(
        teacher_id=teacher_id,
        academic_year="2026-2027",
        week_number=week_number,
        subject_ref=subject_ref,
        class_id=class_id,
        grade_key=grade_key,
        period_number=period_number,
        lesson_title=(
            f"Lesson {period_number}"
        ),
        component_ref=component_ref,
    )


def test_same_grade_classes_form_one_weekly_group():
    service = WeeklyLessonPlanGroupingService()

    result = service.group_for_grade(
        items=(
            item(
                class_id="CLASS-6A1",
                period_number=1,
            ),
            item(
                class_id="CLASS-6A2",
                period_number=2,
            ),
        ),
    )

    assert len(result) == 1

    group = result[0]

    assert (
        group.identity.teaching_scope.grade_key
        == "GRADE-6"
    )

    assert len(group.items) == 2


def test_different_grades_form_different_groups():
    service = WeeklyLessonPlanGroupingService()

    result = service.group_for_grade(
        items=(
            item(
                class_id="CLASS-6A1",
                grade_key="GRADE-6",
            ),
            item(
                class_id="CLASS-7A1",
                grade_key="GRADE-7",
            ),
        ),
    )

    assert len(result) == 2

    assert {
        group.identity.teaching_scope.grade_key
        for group in result
    } == {
        "GRADE-6",
        "GRADE-7",
    }


def test_grade_group_preserves_source_classes():
    service = WeeklyLessonPlanGroupingService()

    result = service.group_for_grade(
        items=(
            item(
                class_id="CLASS-6A1",
                period_number=1,
            ),
            item(
                class_id="CLASS-6A2",
                period_number=2,
            ),
            item(
                class_id="CLASS-6A3",
                period_number=3,
            ),
        ),
    )

    assert len(result) == 1

    assert {
        value.class_id
        for value in result[0].items
    } == {
        "CLASS-6A1",
        "CLASS-6A2",
        "CLASS-6A3",
    }


def test_grade_group_preserves_components():
    service = WeeklyLessonPlanGroupingService()

    result = service.group_for_grade(
        items=(
            item(
                class_id="CLASS-6A1",
                period_number=1,
                component_ref="COMP-A",
            ),
            item(
                class_id="CLASS-6A2",
                period_number=2,
                component_ref="COMP-B",
            ),
        ),
    )

    assert len(result) == 1

    assert {
        value.component_ref
        for value in result[0].items
    } == {
        "COMP-A",
        "COMP-B",
    }


def test_different_subjects_still_split_grade_groups():
    service = WeeklyLessonPlanGroupingService()

    result = service.group_for_grade(
        items=(
            item(
                subject_ref="FOREIGN-LANGUAGE-1",
            ),
            item(
                subject_ref="MATH",
            ),
        ),
    )

    assert len(result) == 2


def test_different_teachers_still_split_grade_groups():
    service = WeeklyLessonPlanGroupingService()

    result = service.group_for_grade(
        items=(
            item(
                teacher_id="GV002",
            ),
            item(
                teacher_id="GV003",
            ),
        ),
    )

    assert len(result) == 2


def test_different_weeks_still_split_grade_groups():
    service = WeeklyLessonPlanGroupingService()

    result = service.group_for_grade(
        items=(
            item(
                week_number=8,
            ),
            item(
                week_number=9,
            ),
        ),
    )

    assert len(result) == 2


def test_grade_key_is_required_not_inferred_from_class_id():
    service = WeeklyLessonPlanGroupingService()

    invalid = ScheduleItem(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="FOREIGN-LANGUAGE-1",
        class_id="CLASS-6A1",
        grade_key="   ",
        period_number=1,
        lesson_title="Lesson 1",
    )

    with pytest.raises(
        ValueError,
        match="grade_key must not be blank",
    ):
        service.group_for_grade(
            items=(invalid,),
        )
