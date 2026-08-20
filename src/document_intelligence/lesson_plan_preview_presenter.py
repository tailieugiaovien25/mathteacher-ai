from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from document_intelligence.contracts import (
    AnalysisSource,
    DocumentField,
)
from document_intelligence.lesson_plan_preview import (
    LessonPlanIntelligencePreview,
)
from document_intelligence.validation import (
    ValidatedDocumentAnalysis,
    ValidationStatus,
)


class PreviewReviewState(str, Enum):
    ACCEPTED = "accepted"
    REVIEW = "review"
    CONFLICT = "conflict"


@dataclass(frozen=True)
class LessonPlanPreviewItemView:
    field: DocumentField
    field_label: str
    value: str
    confidence: float
    confidence_percent: int
    source: AnalysisSource
    source_label: str
    evidence: str
    validation_status: ValidationStatus
    review_state: PreviewReviewState
    requires_review: bool


@dataclass(frozen=True)
class LessonPlanPreviewViewModel:
    items: tuple[LessonPlanPreviewItemView, ...]
    ai_used: bool
    ai_failed: bool
    requires_review: bool
    conflict_count: int


class LessonPlanPreviewPresenter:
    """
    Convert preview and validated analysis into a UI-safe view model.

    Validation is performed outside the presenter.

    No Streamlit rendering, document mutation, persistence,
    AI execution, validation execution, or Word processing
    belongs here.
    """

    _FIELD_LABELS = {
        DocumentField.CLASS_NAME: "Lớp",
        DocumentField.LESSON_TITLE: "Tên bài",
        DocumentField.CURRICULUM_PERIOD: "Tiết",
        DocumentField.DRAFTING_DATE: "Ngày soạn",
        DocumentField.TEACHING_DATE: "Ngày dạy",
    }

    _SOURCE_LABELS = {
        AnalysisSource.DETERMINISTIC: "Quy tắc",
        AnalysisSource.AI: "AI",
    }

    def present(
        self,
        *,
        preview: LessonPlanIntelligencePreview,
        validation: ValidatedDocumentAnalysis,
    ) -> LessonPlanPreviewViewModel:
        items = tuple(
            self._present_item(item)
            for item in validation.proposals
        )

        return LessonPlanPreviewViewModel(
            items=items,
            ai_used=preview.ai_used,
            ai_failed=preview.ai_failed,
            requires_review=any(
                item.requires_review
                for item in items
            ),
            conflict_count=sum(
                item.review_state
                is PreviewReviewState.CONFLICT
                for item in items
            ),
        )

    def _present_item(
        self,
        item,
    ) -> LessonPlanPreviewItemView:
        proposal = item.proposal

        review_state = self._review_state(
            item.status
        )

        return LessonPlanPreviewItemView(
            field=proposal.field,
            field_label=self._FIELD_LABELS.get(
                proposal.field,
                proposal.field.value,
            ),
            value=proposal.value,
            confidence=proposal.confidence,
            confidence_percent=round(
                proposal.confidence * 100
            ),
            source=proposal.source,
            source_label=self._SOURCE_LABELS.get(
                proposal.source,
                proposal.source.value,
            ),
            evidence=proposal.evidence,
            validation_status=item.status,
            review_state=review_state,
            requires_review=(
                review_state
                is not PreviewReviewState.ACCEPTED
            ),
        )

    @staticmethod
    def _review_state(
        status: ValidationStatus,
    ) -> PreviewReviewState:
        if status is ValidationStatus.ACCEPTED:
            return PreviewReviewState.ACCEPTED

        if status is ValidationStatus.CONFLICT:
            return PreviewReviewState.CONFLICT

        return PreviewReviewState.REVIEW
