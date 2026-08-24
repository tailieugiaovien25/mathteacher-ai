import pytest

from lesson_planning_v2.lesson_plan_teaching_scope import (
    LessonPlanTeachingScope,
)
from lesson_planning_v2.weekly_lesson_plan_identity import (
    WeeklyLessonPlanIdentity,
)


def class_scope():
    return LessonPlanTeachingScope.for_class(
        class_id="CLASS-6A1",
    )


def grade_scope():
    return LessonPlanTeachingScope.for_grade(
        grade_key="GRADE-6",
    )


def test_identity_contains_full_weekly_scope():
    identity = WeeklyLessonPlanIdentity(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="FOREIGN-LANGUAGE-1",
        teaching_scope=class_scope(),
    )

    assert identity.teacher_id == "GV002"
    assert identity.academic_year == "2026-2027"
    assert identity.week_number == 8

    assert (
        identity.subject_ref
        == "FOREIGN-LANGUAGE-1"
    )

    assert (
        identity.teaching_scope.class_id
        == "CLASS-6A1"
    )


def test_identity_normalizes_string_fields():
    identity = WeeklyLessonPlanIdentity(
        teacher_id="  GV002  ",
        academic_year="  2026-2027  ",
        week_number=8,
        subject_ref="  FOREIGN-LANGUAGE-1  ",
        teaching_scope=class_scope(),
    )

    assert identity.teacher_id == "GV002"
    assert identity.academic_year == "2026-2027"

    assert (
        identity.subject_ref
        == "FOREIGN-LANGUAGE-1"
    )


def test_identity_key_is_stable_for_class():
    identity = WeeklyLessonPlanIdentity(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="FOREIGN-LANGUAGE-1",
        teaching_scope=class_scope(),
    )

    assert identity.identity_key == (
        "GV002",
        "2026-2027",
        8,
        "FOREIGN-LANGUAGE-1",
        "class",
        "CLASS-6A1",
    )


def test_identity_key_is_stable_for_grade():
    identity = WeeklyLessonPlanIdentity(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="FOREIGN-LANGUAGE-1",
        teaching_scope=grade_scope(),
    )

    assert identity.identity_key == (
        "GV002",
        "2026-2027",
        8,
        "FOREIGN-LANGUAGE-1",
        "grade",
        "GRADE-6",
    )


def test_class_and_grade_are_different_identities():
    class_identity = WeeklyLessonPlanIdentity(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="FOREIGN-LANGUAGE-1",
        teaching_scope=class_scope(),
    )

    grade_identity = WeeklyLessonPlanIdentity(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="FOREIGN-LANGUAGE-1",
        teaching_scope=grade_scope(),
    )

    assert (
        class_identity.identity_key
        != grade_identity.identity_key
    )


def test_different_weeks_are_different_identities():
    week_8 = WeeklyLessonPlanIdentity(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="FOREIGN-LANGUAGE-1",
        teaching_scope=class_scope(),
    )

    week_9 = WeeklyLessonPlanIdentity(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=9,
        subject_ref="FOREIGN-LANGUAGE-1",
        teaching_scope=class_scope(),
    )

    assert (
        week_8.identity_key
        != week_9.identity_key
    )


def test_different_subjects_are_different_identities():
    english = WeeklyLessonPlanIdentity(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="FOREIGN-LANGUAGE-1",
        teaching_scope=class_scope(),
    )

    math = WeeklyLessonPlanIdentity(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="MATH",
        teaching_scope=class_scope(),
    )

    assert (
        english.identity_key
        != math.identity_key
    )


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    (
        (
            "teacher_id",
            "   ",
            "teacher_id must not be blank",
        ),
        (
            "academic_year",
            "   ",
            "academic_year must not be blank",
        ),
        (
            "subject_ref",
            "   ",
            "subject_ref must not be blank",
        ),
    ),
)
def test_blank_identity_fields_are_rejected(
    field_name,
    value,
    message,
):
    kwargs = {
        "teacher_id": "GV002",
        "academic_year": "2026-2027",
        "week_number": 8,
        "subject_ref": "FOREIGN-LANGUAGE-1",
        "teaching_scope": class_scope(),
    }

    kwargs[field_name] = value

    with pytest.raises(
        ValueError,
        match=message,
    ):
        WeeklyLessonPlanIdentity(
            **kwargs
        )


@pytest.mark.parametrize(
    "week_number",
    (
        0,
        -1,
    ),
)
def test_invalid_week_number_is_rejected(
    week_number,
):
    with pytest.raises(
        ValueError,
        match="week_number must be positive",
    ):
        WeeklyLessonPlanIdentity(
            teacher_id="GV002",
            academic_year="2026-2027",
            week_number=week_number,
            subject_ref="FOREIGN-LANGUAGE-1",
            teaching_scope=class_scope(),
        )
