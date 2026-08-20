from pathlib import Path

from document_intelligence.contracts import (
    AnalysisSource,
    DocumentAnalysis,
    DocumentField,
    DocumentFieldProposal,
)
from document_intelligence.lesson_plan_preview import (
    LessonPlanIntelligencePreview,
)
from document_intelligence.lesson_plan_preview_presenter import (
    LessonPlanPreviewPresenter,
    PreviewReviewState,
)
from document_intelligence.validation import (
    CanonicalDocumentContext,
    DocumentAnalysisValidator,
)


def proposal(
    *,
    field,
    value,
    confidence,
    source,
    evidence="",
):
    return DocumentFieldProposal(
        field=field,
        value=value,
        confidence=confidence,
        source=source,
        evidence=evidence,
    )


def make_preview(
    *,
    proposals,
    ai_used=False,
    ai_failed=False,
):
    analysis = DocumentAnalysis(
        proposals=tuple(proposals)
    )

    return LessonPlanIntelligencePreview(
        source=Path("lesson.docx"),
        document_text="",
        analysis=analysis,
        ai_used=ai_used,
        ai_failed=ai_failed,
    )


def validate(
    *,
    preview,
    canonical,
):
    return DocumentAnalysisValidator().validate(
        analysis=preview.analysis,
        canonical=canonical,
    )


def test_presenter_maps_accepted_proposal():
    preview = make_preview(
        proposals=(
            proposal(
                field=DocumentField.CLASS_NAME,
                value="6A1",
                confidence=0.99,
                source=AnalysisSource.DETERMINISTIC,
                evidence="Lớp: 6A1",
            ),
        ),
    )

    validation = validate(
        preview=preview,
        canonical=CanonicalDocumentContext(
            class_name="6A1"
        ),
    )

    view = LessonPlanPreviewPresenter().present(
        preview=preview,
        validation=validation,
    )

    assert len(view.items) == 1

    item = view.items[0]

    assert item.field is DocumentField.CLASS_NAME
    assert item.field_label == "Lớp"
    assert item.value == "6A1"
    assert item.confidence == 0.99
    assert item.confidence_percent == 99
    assert item.source is AnalysisSource.DETERMINISTIC
    assert item.source_label == "Quy tắc"
    assert item.evidence == "Lớp: 6A1"
    assert (
        item.review_state
        is PreviewReviewState.ACCEPTED
    )
    assert item.requires_review is False

    assert view.requires_review is False
    assert view.conflict_count == 0


def test_presenter_marks_conflict_for_review():
    preview = make_preview(
        proposals=(
            proposal(
                field=DocumentField.CLASS_NAME,
                value="6A2",
                confidence=0.95,
                source=AnalysisSource.AI,
                evidence="Lớp 6A2",
            ),
        ),
        ai_used=True,
    )

    validation = validate(
        preview=preview,
        canonical=CanonicalDocumentContext(
            class_name="6A1"
        ),
    )

    view = LessonPlanPreviewPresenter().present(
        preview=preview,
        validation=validation,
    )

    item = view.items[0]

    assert item.source_label == "AI"
    assert (
        item.review_state
        is PreviewReviewState.CONFLICT
    )
    assert item.requires_review is True

    assert view.ai_used is True
    assert view.requires_review is True
    assert view.conflict_count == 1


def test_presenter_marks_unverified_for_review():
    preview = make_preview(
        proposals=(
            proposal(
                field=DocumentField.LESSON_TITLE,
                value="Đơn thức",
                confidence=0.88,
                source=AnalysisSource.AI,
            ),
        ),
    )

    validation = validate(
        preview=preview,
        canonical=CanonicalDocumentContext(),
    )

    view = LessonPlanPreviewPresenter().present(
        preview=preview,
        validation=validation,
    )

    item = view.items[0]

    assert (
        item.review_state
        is PreviewReviewState.REVIEW
    )
    assert item.requires_review is True
    assert view.requires_review is True


def test_presenter_preserves_ai_failure_state():
    preview = make_preview(
        proposals=(),
        ai_used=True,
        ai_failed=True,
    )

    validation = validate(
        preview=preview,
        canonical=CanonicalDocumentContext(),
    )

    view = LessonPlanPreviewPresenter().present(
        preview=preview,
        validation=validation,
    )

    assert view.ai_used is True
    assert view.ai_failed is True
    assert view.items == ()
    assert view.requires_review is False
    assert view.conflict_count == 0


def test_presenter_does_not_modify_inputs():
    preview = make_preview(
        proposals=(
            proposal(
                field=DocumentField.LESSON_TITLE,
                value="Đơn thức",
                confidence=0.96,
                source=AnalysisSource.AI,
            ),
        ),
    )

    validation = validate(
        preview=preview,
        canonical=CanonicalDocumentContext(
            lesson_title="Đơn thức"
        ),
    )

    original_analysis = preview.analysis
    original_validation = validation

    LessonPlanPreviewPresenter().present(
        preview=preview,
        validation=validation,
    )

    assert preview.analysis is original_analysis
    assert validation is original_validation
