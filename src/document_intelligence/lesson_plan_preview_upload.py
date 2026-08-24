from __future__ import annotations

import os
import tempfile
from pathlib import Path

from document_intelligence import (
    build_document_analyzer,
)
from document_intelligence.lesson_plan_preview import (
    LessonPlanIntelligencePreviewService,
)
from document_intelligence.lesson_plan_preview_application import (
    LessonPlanPreviewApplicationService,
)
from document_intelligence.lesson_plan_preview_presenter import (
    LessonPlanPreviewViewModel,
)
from document_intelligence.validation import (
    CanonicalDocumentContext,
)


class LessonPlanPreviewUploadService:
    """
    Bridge uploaded DOCX bytes into the lesson-plan preview pipeline.

    The temporary file exists only because the existing preview service
    operates on a Path. It is removed after preview preparation.

    No Streamlit rendering or document mutation belongs here.
    """

    def __init__(
        self,
        *,
        application_service: (
            LessonPlanPreviewApplicationService
            | None
        ) = None,
    ) -> None:
        self._application_service = (
            application_service
            if application_service is not None
            else LessonPlanPreviewApplicationService(
                preview_service=(
                    LessonPlanIntelligencePreviewService(
                        analyzer=build_document_analyzer()
                    )
                )
            )
        )

    def prepare(
        self,
        *,
        content: bytes,
        canonical: CanonicalDocumentContext,
    ) -> LessonPlanPreviewViewModel:
        if not isinstance(
            content,
            bytes,
        ):
            raise TypeError(
                "content must be bytes"
            )

        if not content:
            raise ValueError(
                "content must not be empty"
            )

        if not isinstance(
            canonical,
            CanonicalDocumentContext,
        ):
            raise TypeError(
                "canonical must be CanonicalDocumentContext"
            )

        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".docx",
                delete=False,
            ) as temporary:
                temporary.write(content)
                temporary.flush()

                temporary_path = Path(
                    temporary.name
                )

            return self._application_service.prepare(
                source=temporary_path,
                canonical=canonical,
            )

        finally:
            if (
                temporary_path is not None
                and temporary_path.exists()
            ):
                os.unlink(
                    temporary_path
                )
