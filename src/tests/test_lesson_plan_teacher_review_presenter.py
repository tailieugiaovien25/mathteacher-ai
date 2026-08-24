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


def test_presenter_emits_at_most_one_review_item_per_field():
    preview = LessonPlanPreviewViewModel(
        items=(
            make_item(
                field=DocumentField.CLASS_NAME,
                field_label="Lớp",
                value="6A2",
                validation_status=(
                    ValidationStatus.CONFLICT
                ),
                review_state=(
                    PreviewReviewState.CONFLICT
                ),
                requires_review=True,
            ),
            make_item(
                field=DocumentField.CLASS_NAME,
                field_label="Lớp",
                value="-",
                validation_status=(
                    ValidationStatus.CONFLICT
                ),
                review_state=(
                    PreviewReviewState.CONFLICT
                ),
                requires_review=True,
            ),
            make_item(
                field=DocumentField.CLASS_NAME,
                field_label="Lớp",
                value="ho",
                validation_status=(
                    ValidationStatus.CONFLICT
                ),
                review_state=(
                    PreviewReviewState.CONFLICT
                ),
                requires_review=True,
            ),
            make_item(
                field=DocumentField.LESSON_TITLE,
                field_label="Tên bài",
                value="Bài 7",
                validation_status=(
                    ValidationStatus.ACCEPTED
                ),
                review_state=(
                    PreviewReviewState.ACCEPTED
                ),
                requires_review=False,
            ),
        ),
        ai_used=False,
        ai_failed=False,
        requires_review=True,
        conflict_count=3,
    )

    view = (
        LessonPlanTeacherReviewPresenter()
        .present(
            preview=preview,
            canonical_values={
                DocumentField.CLASS_NAME: "6A1",
                DocumentField.LESSON_TITLE: (
                    "Bài 7"
                ),
            },
        )
    )

    fields = tuple(
        item.field
        for item in view.items
    )

    assert (
        len(fields)
        == len(set(fields))
    )

    assert (
        fields.count(
            DocumentField.CLASS_NAME
        )
        == 1
    )


def test_presenter_prefers_candidate_matching_canonical_value():
    preview = LessonPlanPreviewViewModel(
        items=(
            make_item(
                field=DocumentField.CLASS_NAME,
                field_label="Lớp",
                value="6A2",
                validation_status=(
                    ValidationStatus.CONFLICT
                ),
                review_state=(
                    PreviewReviewState.CONFLICT
                ),
                requires_review=True,
            ),
            make_item(
                field=DocumentField.CLASS_NAME,
                field_label="Lớp",
                value="6A1",
                validation_status=(
                    ValidationStatus.ACCEPTED
                ),
                review_state=(
                    PreviewReviewState.ACCEPTED
                ),
                requires_review=False,
            ),
        ),
        ai_used=False,
        ai_failed=False,
        requires_review=True,
        conflict_count=1,
    )

    view = (
        LessonPlanTeacherReviewPresenter()
        .present(
            preview=preview,
            canonical_values={
                DocumentField.CLASS_NAME: "6A1",
            },
        )
    )

    assert len(view.items) == 1

    item = view.items[0]

    assert (
        item.field
        is DocumentField.CLASS_NAME
    )

    assert (
        item.detected_value
        == "6A1"
    )

    assert (
        item.default_action
        is TeacherReviewAction.CONFIRM
    )
