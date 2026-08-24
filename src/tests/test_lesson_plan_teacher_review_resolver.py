import pytest

from document_intelligence.contracts import (
    AnalysisSource,
    DocumentField,
)
from document_intelligence.lesson_plan_preview_presenter import (
    LessonPlanPreviewItemView,
    LessonPlanPreviewViewModel,
    PreviewReviewState,
)
from document_intelligence.lesson_plan_teacher_review import (
    LessonPlanTeacherReview,
    TeacherFieldDecision,
    TeacherReviewAction,
)
from document_intelligence.lesson_plan_teacher_review_resolver import (
    LessonPlanTeacherReviewResolver,
)
from document_intelligence.validation import (
    ValidationStatus,
)


def make_item(
    *,
    field,
    value,
):
    return LessonPlanPreviewItemView(
        field=field,
        field_label=field.value,
        value=value,
        confidence=1.0,
        confidence_percent=100,
        source=AnalysisSource.DETERMINISTIC,
        source_label="rule",
        evidence="",
        validation_status=(
            ValidationStatus.ACCEPTED
        ),
        review_state=(
            PreviewReviewState.ACCEPTED
        ),
        requires_review=False,
    )


def make_preview():
    return LessonPlanPreviewViewModel(
        items=(
            make_item(
                field=DocumentField.CLASS_NAME,
                value="8A2",
            ),
            make_item(
                field=DocumentField.LESSON_TITLE,
                value="Đơn thức",
            ),
        ),
        ai_used=False,
        ai_failed=False,
        requires_review=False,
        conflict_count=0,
    )


def test_resolver_requires_complete_review():
    review = LessonPlanTeacherReview(
        decisions=(
            TeacherFieldDecision(
                field=DocumentField.CLASS_NAME,
                action=TeacherReviewAction.CONFIRM,
                canonical_value="8A2",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="incomplete",
    ):
        LessonPlanTeacherReviewResolver().resolve(
            preview=make_preview(),
            review=review,
        )


def test_resolver_uses_confirmed_values():
    review = LessonPlanTeacherReview(
        decisions=(
            TeacherFieldDecision(
                field=DocumentField.CLASS_NAME,
                action=TeacherReviewAction.CONFIRM,
                canonical_value="8A2",
            ),
            TeacherFieldDecision(
                field=DocumentField.LESSON_TITLE,
                action=TeacherReviewAction.CONFIRM,
                detected_value="Đơn thức",
            ),
        )
    )

    result = (
        LessonPlanTeacherReviewResolver()
        .resolve(
            preview=make_preview(),
            review=review,
        )
    )

    assert result.accepted is True
    assert result.rejected_fields == ()

    assert (
        result.metadata.value_for(
            DocumentField.CLASS_NAME
        )
        == "8A2"
    )

    assert (
        result.metadata.value_for(
            DocumentField.LESSON_TITLE
        )
        == "Đơn thức"
    )


def test_resolver_uses_override_value():
    review = LessonPlanTeacherReview(
        decisions=(
            TeacherFieldDecision(
                field=DocumentField.CLASS_NAME,
                action=TeacherReviewAction.OVERRIDE,
                detected_value="8A2",
                override_value="8A3",
            ),
            TeacherFieldDecision(
                field=DocumentField.LESSON_TITLE,
                action=TeacherReviewAction.CONFIRM,
                detected_value="Đơn thức",
            ),
        )
    )

    result = (
        LessonPlanTeacherReviewResolver()
        .resolve(
            preview=make_preview(),
            review=review,
        )
    )

    assert result.accepted is True

    assert (
        result.metadata.value_for(
            DocumentField.CLASS_NAME
        )
        == "8A3"
    )


def test_resolver_tracks_rejected_field():
    review = LessonPlanTeacherReview(
        decisions=(
            TeacherFieldDecision(
                field=DocumentField.CLASS_NAME,
                action=TeacherReviewAction.REJECT,
                detected_value="8A2",
            ),
            TeacherFieldDecision(
                field=DocumentField.LESSON_TITLE,
                action=TeacherReviewAction.CONFIRM,
                detected_value="Đơn thức",
            ),
        )
    )

    result = (
        LessonPlanTeacherReviewResolver()
        .resolve(
            preview=make_preview(),
            review=review,
        )
    )

    assert result.accepted is False

    assert result.rejected_fields == (
        DocumentField.CLASS_NAME,
    )

    assert (
        result.metadata.value_for(
            DocumentField.CLASS_NAME
        )
        is None
    )


def test_resolver_rejects_invalid_preview():
    with pytest.raises(
        TypeError,
        match="preview must be",
    ):
        LessonPlanTeacherReviewResolver().resolve(
            preview=object(),
            review=LessonPlanTeacherReview(
                decisions=()
            ),
        )


def test_resolver_rejects_invalid_review():
    with pytest.raises(
        TypeError,
        match="review must be",
    ):
        LessonPlanTeacherReviewResolver().resolve(
            preview=make_preview(),
            review=object(),
        )
