from __future__ import annotations

from document_intelligence.contracts import (
    AnalysisSource,
    DocumentAnalysis,
    DocumentField,
    DocumentFieldProposal,
)
from document_intelligence.lesson_plan_recognition import (
    LessonPlanRecognitionEngine,
)


_FIELD_MAP = {
    "drafting_date": DocumentField.DRAFTING_DATE,
    "teaching_date": DocumentField.TEACHING_DATE,
    "class_name": DocumentField.CLASS_NAME,
    "curriculum_period": DocumentField.CURRICULUM_PERIOD,
    "lesson_title": DocumentField.LESSON_TITLE,
}


class DeterministicDocumentAnalyzer:
    """
    Deterministic implementation of DocumentAnalyzer.

    It converts recognition-engine results into structured
    document-intelligence proposals.
    """

    def __init__(
        self,
        *,
        recognition_engine: (
            LessonPlanRecognitionEngine | None
        ) = None,
    ) -> None:
        self._recognition_engine = (
            recognition_engine
            or LessonPlanRecognitionEngine()
        )

    def analyze(
        self,
        *,
        document_text: str,
    ) -> DocumentAnalysis:
        proposals = []

        for line in document_text.splitlines():
            recognized = (
                self._recognition_engine
                .recognize_text(line)
            )

            for item in recognized:
                field = _FIELD_MAP.get(
                    item.field_name
                )

                if field is None:
                    continue

                proposals.append(
                    DocumentFieldProposal(
                        field=field,
                        value=item.value,
                        confidence=self._confidence_for(
                            field
                        ),
                        source=(
                            AnalysisSource.DETERMINISTIC
                        ),
                        evidence=item.evidence,
                    )
                )

        return DocumentAnalysis(
            proposals=tuple(proposals)
        )

    @staticmethod
    def _confidence_for(
        field: DocumentField,
    ) -> float:
        if field in (
            DocumentField.DRAFTING_DATE,
            DocumentField.TEACHING_DATE,
            DocumentField.CLASS_NAME,
            DocumentField.CURRICULUM_PERIOD,
        ):
            return 0.99

        if field is DocumentField.LESSON_TITLE:
            return 0.95

        return 0.90
