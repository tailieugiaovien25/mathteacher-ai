import pytest

from lesson_planning_v2.lesson_plan_teaching_scope import (
    LessonPlanTeachingScope,
    LessonPlanTeachingScopeType,
)


def test_class_scope_has_canonical_identity():
    scope = LessonPlanTeachingScope.for_class(
        class_id="CLASS-6A1",
    )

    assert (
        scope.scope_type
        == LessonPlanTeachingScopeType.CLASS
    )

    assert scope.scope_ref == "CLASS-6A1"
    assert scope.class_id == "CLASS-6A1"
    assert scope.grade_key is None


def test_grade_scope_has_canonical_identity():
    scope = LessonPlanTeachingScope.for_grade(
        grade_key="GRADE-6",
    )

    assert (
        scope.scope_type
        == LessonPlanTeachingScopeType.GRADE
    )

    assert scope.scope_ref == "GRADE-6"
    assert scope.class_id is None
    assert scope.grade_key == "GRADE-6"


def test_class_scope_normalizes_value():
    scope = LessonPlanTeachingScope.for_class(
        class_id="  CLASS-6A1  ",
    )

    assert scope.scope_ref == "CLASS-6A1"


def test_grade_scope_normalizes_value():
    scope = LessonPlanTeachingScope.for_grade(
        grade_key="  GRADE-6  ",
    )

    assert scope.scope_ref == "GRADE-6"


def test_blank_class_scope_is_rejected():
    with pytest.raises(
        ValueError,
        match="class_id must not be blank",
    ):
        LessonPlanTeachingScope.for_class(
            class_id="   ",
        )


def test_blank_grade_scope_is_rejected():
    with pytest.raises(
        ValueError,
        match="grade_key must not be blank",
    ):
        LessonPlanTeachingScope.for_grade(
            grade_key="   ",
        )


def test_scope_identity_distinguishes_class_and_grade():
    class_scope = (
        LessonPlanTeachingScope.for_class(
            class_id="6",
        )
    )

    grade_scope = (
        LessonPlanTeachingScope.for_grade(
            grade_key="6",
        )
    )

    assert (
        class_scope.identity_key
        != grade_scope.identity_key
    )


def test_class_scope_identity_is_stable():
    scope = LessonPlanTeachingScope.for_class(
        class_id="CLASS-6A1",
    )

    assert scope.identity_key == (
        "class",
        "CLASS-6A1",
    )


def test_grade_scope_identity_is_stable():
    scope = LessonPlanTeachingScope.for_grade(
        grade_key="GRADE-6",
    )

    assert scope.identity_key == (
        "grade",
        "GRADE-6",
    )
