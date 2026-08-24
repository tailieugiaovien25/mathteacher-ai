from __future__ import annotations

from pathlib import Path

from document_intelligence.lesson_plan_preview import (
    LessonPlanIntelligencePreviewService,
)
from document_intelligence.lesson_plan_preview_presenter import (
    LessonPlanPreviewPresenter,
    LessonPlanPreviewViewModel,
)
from document_intelligence.validation import (
    CanonicalDocumentContext,
    DocumentAnalysisValidator,
)


class LessonPlanPreviewApplicationService:
    """
    Application boundary for lesson-plan intelligence preview.

    Responsibilities:
    - request a read-only intelligence preview;
    - validate proposals against canonical context;
    - present validated results as a UI-safe view model.

    It does not render Streamlit UI and does not mutate DOCX files.
    """

    def __init__(
        self,
        *,
        preview_service: LessonPlanIntelligencePreviewService,
        validator: DocumentAnalysisValidator | None = None,
        presenter: LessonPlanPreviewPresenter | None = None,
    ) -> None:
        if not isinstance(
            preview_service,
            LessonPlanIntelligencePreviewService,
        ):
            raise TypeError(
                "preview_service must be "
                "LessonPlanIntelligencePreviewService"
            )

        if (
            validator is not None
            and not isinstance(
                validator,
                DocumentAnalysisValidator,
            )
        ):
            raise TypeError(
                "validator must be "
                "DocumentAnalysisValidator or None"
            )

        if (
            presenter is not None
            and not isinstance(
                presenter,
                LessonPlanPreviewPresenter,
            )
        ):
            raise TypeError(
                "presenter must be "
                "LessonPlanPreviewPresenter or None"
            )

        self._preview_service = preview_service
        self._validator = (
            validator
            if validator is not None
            else DocumentAnalysisValidator()
        )
        self._presenter = (
            presenter
            if presenter is not None
            else LessonPlanPreviewPresenter()
        )

    def prepare(
        self,
        *,
        source: Path,
        canonical: CanonicalDocumentContext,
    ) -> LessonPlanPreviewViewModel:
        if not isinstance(
            canonical,
            CanonicalDocumentContext,
        ):
            raise TypeError(
                "canonical must be CanonicalDocumentContext"
            )

        source = Path(source)

        preview = self._preview_service.preview(
            source=source
        )

        validation = self._validator.validate(
            analysis=preview.analysis,
            canonical=canonical,
        )

        return self._presenter.present(
            preview=preview,
            validation=validation,
        )
