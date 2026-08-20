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
    TeacherReviewAction,
)
from document_intelligence.lesson_plan_teacher_review_presenter import (
    LessonPlanTeacherReviewPresenter,
)
from document_intelligence.validation import (
    ValidationStatus,
)


def make_item(
    *,
    field,
    field_label,
    value,
    validation_status,
    review_state,
    requires_review,
):
    return LessonPlanPreviewItemView(
        field=field,
        field_label=field_label,
        value=value,
        confidence=1.0,
        confidence_percent=100,
        source=AnalysisSource.DETERMINISTIC,
        source_label="rule",
        evidence="",
        validation_status=validation_status,
        review_state=review_state,
        requires_review=requires_review,
    )


def make_preview():
    return LessonPlanPreviewViewModel(
        items=(
            make_item(
                field=DocumentField.CLASS_NAME,
                field_label="Lớp",
                value="8A2",
                validation_status=(
                    ValidationStatus.ACCEPTED
                ),
                review_state=(
                    PreviewReviewState.ACCEPTED
                ),
                requires_review=False,
            ),
            make_item(
                field=DocumentField.LESSON_TITLE,
                field_label="Tên bài",
                value="Đơn thức",
                validation_status=(
                    ValidationStatus.CONFLICT
                ),
                review_state=(
                    PreviewReviewState.CONFLICT
                ),
                requires_review=True,
            ),
        ),
        ai_used=False,
        ai_failed=False,
        requires_review=True,
        conflict_count=1,
    )


def test_presenter_maps_review_items():
    view = (
        LessonPlanTeacherReviewPresenter()
        .present(
            preview=make_preview(),
            canonical_values={
                DocumentField.CLASS_NAME: "8A2",
                DocumentField.LESSON_TITLE: (
                    "Đơn thức chuẩn"
                ),
            },
        )
    )

    assert len(view.items) == 2
    assert view.requires_review is True

    first = view.items[0]

    assert (
        first.field
        is DocumentField.CLASS_NAME
    )
    assert first.field_label == "Lớp"
    assert first.detected_value == "8A2"
    assert first.canonical_value == "8A2"
    assert (
        first.default_action
        is TeacherReviewAction.CONFIRM
    )


def test_presenter_defaults_conflict_to_reject():
    view = (
        LessonPlanTeacherReviewPresenter()
        .present(
            preview=make_preview(),
            canonical_values={
                DocumentField.CLASS_NAME: "8A2",
                DocumentField.LESSON_TITLE: (
                    "Đơn thức chuẩn"
                ),
            },
        )
    )

    conflict = view.items[1]

    assert (
        conflict.review_state
        is PreviewReviewState.CONFLICT
    )
    assert conflict.requires_review is True
    assert (
        conflict.default_action
        is TeacherReviewAction.REJECT
    )


def test_presenter_allows_missing_canonical():
    view = (
        LessonPlanTeacherReviewPresenter()
        .present(
            preview=make_preview(),
            canonical_values={},
        )
    )

    assert (
        view.items[1].canonical_value
        is None
    )


def test_presenter_rejects_invalid_preview():
    with pytest.raises(
        TypeError,
        match="preview must be",
    ):
        (
            LessonPlanTeacherReviewPresenter()
            .present(
                preview=object(),
                canonical_values={},
            )
        )


def test_presenter_rejects_invalid_canonical_values():
    with pytest.raises(
        TypeError,
        match="canonical_values must be dict",
    ):
        (
            LessonPlanTeacherReviewPresenter()
            .present(
                preview=make_preview(),
                canonical_values=object(),
            )
        )
