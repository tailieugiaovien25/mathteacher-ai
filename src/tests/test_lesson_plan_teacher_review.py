import pytest

from document_intelligence.contracts import (
    DocumentField,
)
from document_intelligence.lesson_plan_teacher_review import (
    LessonPlanTeacherReview,
    TeacherFieldDecision,
    TeacherReviewAction,
)


def test_confirm_uses_canonical_value():
    decision = TeacherFieldDecision(
        field=DocumentField.CLASS_NAME,
        action=TeacherReviewAction.CONFIRM,
        detected_value="8A2",
        canonical_value="8A1",
    )

    assert decision.is_accepted is True
    assert decision.resolved_value == "8A1"


def test_confirm_falls_back_to_detected_value():
    decision = TeacherFieldDecision(
        field=DocumentField.LESSON_TITLE,
        action=TeacherReviewAction.CONFIRM,
        detected_value="Đơn thức",
    )

    assert decision.resolved_value == "Đơn thức"


def test_override_requires_explicit_value():
    with pytest.raises(
        ValueError,
        match="override_value",
    ):
        TeacherFieldDecision(
            field=DocumentField.CLASS_NAME,
            action=TeacherReviewAction.OVERRIDE,
            detected_value="8A2",
        )


def test_override_uses_teacher_value():
    decision = TeacherFieldDecision(
        field=DocumentField.CLASS_NAME,
        action=TeacherReviewAction.OVERRIDE,
        detected_value="8A2",
        canonical_value="8A1",
        override_value=" 8A3 ",
    )

    assert decision.is_accepted is True
    assert decision.resolved_value == "8A3"


def test_reject_has_no_resolved_value():
    decision = TeacherFieldDecision(
        field=DocumentField.CLASS_NAME,
        action=TeacherReviewAction.REJECT,
        detected_value="8A2",
        canonical_value="8A1",
    )

    assert decision.is_accepted is False
    assert decision.resolved_value is None


def test_non_override_cannot_supply_override_value():
    with pytest.raises(
        ValueError,
        match="only valid",
    ):
        TeacherFieldDecision(
            field=DocumentField.CLASS_NAME,
            action=TeacherReviewAction.CONFIRM,
            override_value="8A3",
        )


def test_review_rejects_duplicate_fields():
    first = TeacherFieldDecision(
        field=DocumentField.CLASS_NAME,
        action=TeacherReviewAction.CONFIRM,
        detected_value="8A1",
    )

    second = TeacherFieldDecision(
        field=DocumentField.CLASS_NAME,
        action=TeacherReviewAction.REJECT,
        detected_value="8A2",
    )

    with pytest.raises(
        ValueError,
        match="duplicate",
    ):
        LessonPlanTeacherReview(
            decisions=(
                first,
                second,
            )
        )


def test_review_reports_acceptance():
    review = LessonPlanTeacherReview(
        decisions=(
            TeacherFieldDecision(
                field=DocumentField.CLASS_NAME,
                action=TeacherReviewAction.CONFIRM,
                canonical_value="8A1",
            ),
            TeacherFieldDecision(
                field=DocumentField.LESSON_TITLE,
                action=TeacherReviewAction.OVERRIDE,
                detected_value="Đơn thức cũ",
                override_value="Đơn thức",
            ),
        )
    )

    assert review.is_accepted is True


def test_review_reports_rejection():
    review = LessonPlanTeacherReview(
        decisions=(
            TeacherFieldDecision(
                field=DocumentField.CLASS_NAME,
                action=TeacherReviewAction.REJECT,
                detected_value="8A2",
            ),
        )
    )

    assert review.is_accepted is False


def test_decision_for_returns_matching_field():
    decision = TeacherFieldDecision(
        field=DocumentField.CLASS_NAME,
        action=TeacherReviewAction.CONFIRM,
        canonical_value="8A1",
    )

    review = LessonPlanTeacherReview(
        decisions=(decision,)
    )

    assert (
        review.decision_for(
            DocumentField.CLASS_NAME
        )
        is decision
    )

    assert (
        review.decision_for(
            DocumentField.LESSON_TITLE
        )
        is None
    )
