import pytest

from document_intelligence.contracts import (
    DocumentField,
)
from document_intelligence.lesson_plan_modification_plan import (
    LessonPlanFieldModification,
    LessonPlanModificationPlan,
    LessonPlanModificationPlanner,
)
from document_intelligence.lesson_plan_teacher_review_resolver import (
    LessonPlanTeacherReviewResolution,
    ResolvedLessonPlanMetadata,
)


def make_resolution(
    *,
    accepted=True,
):
    return LessonPlanTeacherReviewResolution(
        accepted=accepted,
        metadata=ResolvedLessonPlanMetadata(
            values=(
                (
                    DocumentField.CLASS_NAME,
                    " 8A1 ",
                ),
                (
                    DocumentField.CURRICULUM_PERIOD,
                    " 9 ",
                ),
                (
                    DocumentField.LESSON_TITLE,
                    " Đơn thức ",
                ),
            )
        ),
        rejected_fields=(),
    )


def test_field_modification_normalizes_value():
    modification = LessonPlanFieldModification(
        field=DocumentField.LESSON_TITLE,
        value="  Đơn thức  ",
    )

    assert modification.value == "Đơn thức"


def test_field_modification_rejects_empty_value():
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        LessonPlanFieldModification(
            field=DocumentField.LESSON_TITLE,
            value="   ",
        )


def test_plan_returns_value_for_field():
    plan = LessonPlanModificationPlan(
        modifications=(
            LessonPlanFieldModification(
                field=DocumentField.CLASS_NAME,
                value="8A1",
            ),
        )
    )

    assert (
        plan.value_for(
            DocumentField.CLASS_NAME
        )
        == "8A1"
    )

    assert (
        plan.value_for(
            DocumentField.LESSON_TITLE
        )
        is None
    )


def test_empty_plan_reports_empty():
    plan = LessonPlanModificationPlan()

    assert plan.is_empty


def test_planner_builds_plan_from_accepted_resolution():
    plan = (
        LessonPlanModificationPlanner()
        .build(
            resolution=make_resolution()
        )
    )

    assert not plan.is_empty

    assert (
        plan.value_for(
            DocumentField.CLASS_NAME
        )
        == "8A1"
    )

    assert (
        plan.value_for(
            DocumentField.CURRICULUM_PERIOD
        )
        == "9"
    )

    assert (
        plan.value_for(
            DocumentField.LESSON_TITLE
        )
        == "Đơn thức"
    )


def test_planner_rejects_unaccepted_resolution():
    with pytest.raises(
        ValueError,
        match="must be accepted",
    ):
        (
            LessonPlanModificationPlanner()
            .build(
                resolution=make_resolution(
                    accepted=False
                )
            )
        )


def test_planner_rejects_wrong_resolution_type():
    with pytest.raises(
        TypeError,
        match="LessonPlanTeacherReviewResolution",
    ):
        (
            LessonPlanModificationPlanner()
            .build(
                resolution=object()
            )
        )


def test_planner_builds_directly_from_canonical_values():
    values = {
        DocumentField.CLASS_NAME: "6A1",
        DocumentField.CURRICULUM_PERIOD: "4",
        DocumentField.LESSON_TITLE: "B?i 7",
        DocumentField.DRAFTING_DATE: "09/09/2026",
        DocumentField.TEACHING_DATE: "10/09/2026",
    }

    plan = (
        LessonPlanModificationPlanner()
        .build_from_values(
            values=values
        )
    )

    assert (
        plan.value_for(
            DocumentField.CLASS_NAME
        )
        == "6A1"
    )

    assert (
        plan.value_for(
            DocumentField.CURRICULUM_PERIOD
        )
        == "4"
    )

    assert (
        plan.value_for(
            DocumentField.LESSON_TITLE
        )
        == "B?i 7"
    )

    assert (
        plan.value_for(
            DocumentField.DRAFTING_DATE
        )
        == "09/09/2026"
    )

    assert (
        plan.value_for(
            DocumentField.TEACHING_DATE
        )
        == "10/09/2026"
    )


def test_direct_plan_does_not_require_teacher_review():
    values = {
        DocumentField.CLASS_NAME: "6A1",
    }

    plan = (
        LessonPlanModificationPlanner()
        .build_from_values(
            values=values
        )
    )

    assert not plan.is_empty


def test_direct_plan_ignores_empty_optional_values():
    values = {
        DocumentField.CLASS_NAME: "6A1",
        DocumentField.LESSON_TITLE: "",
    }

    plan = (
        LessonPlanModificationPlanner()
        .build_from_values(
            values=values
        )
    )

    assert (
        plan.value_for(
            DocumentField.CLASS_NAME
        )
        == "6A1"
    )

    assert (
        plan.value_for(
            DocumentField.LESSON_TITLE
        )
        is None
    )
