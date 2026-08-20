from __future__ import annotations

from dataclasses import dataclass

from document_intelligence.contracts import (
    DocumentAnalysis,
    DocumentAnalyzer,
    DocumentField,
)


@dataclass(frozen=True)
class HybridAnalysisResult:
    analysis: DocumentAnalysis
    ai_used: bool
    ai_error: str | None = None


class HybridDocumentAnalyzer:
    def __init__(
        self,
        *,
        deterministic_analyzer: DocumentAnalyzer,
        ai_analyzer: DocumentAnalyzer | None = None,
        required_fields: tuple[DocumentField, ...] = (
            DocumentField.DRAFTING_DATE,
            DocumentField.TEACHING_DATE,
            DocumentField.CLASS_NAME,
            DocumentField.CURRICULUM_PERIOD,
            DocumentField.LESSON_TITLE,
        ),
        confidence_threshold: float = 0.90,
    ) -> None:
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError(
                "confidence_threshold must be between 0.0 and 1.0"
            )

        self._deterministic_analyzer = deterministic_analyzer
        self._ai_analyzer = ai_analyzer
        self._required_fields = required_fields
        self._confidence_threshold = confidence_threshold

    def analyze(
        self,
        *,
        document_text: str,
    ) -> HybridAnalysisResult:
        deterministic = (
            self._deterministic_analyzer.analyze(
                document_text=document_text
            )
        )

        missing_or_weak = (
            self._missing_or_weak_fields(
                deterministic
            )
        )

        if (
            not missing_or_weak
            or self._ai_analyzer is None
        ):
            return HybridAnalysisResult(
                analysis=deterministic,
                ai_used=False,
            )

        try:
            ai_analysis = self._ai_analyzer.analyze(
                document_text=document_text
            )
        except Exception as error:
            return HybridAnalysisResult(
                analysis=deterministic,
                ai_used=True,
                ai_error=str(error),
            )

        merged = self._merge(
            deterministic=deterministic,
            ai=ai_analysis,
            allowed_ai_fields=missing_or_weak,
        )

        return HybridAnalysisResult(
            analysis=merged,
            ai_used=True,
        )

    def _missing_or_weak_fields(
        self,
        analysis: DocumentAnalysis,
    ) -> tuple[DocumentField, ...]:
        result = []

        for field in self._required_fields:
            proposals = analysis.for_field(field)

            if not proposals:
                result.append(field)
                continue

            strongest = max(
                proposal.confidence
                for proposal in proposals
            )

            if strongest < self._confidence_threshold:
                result.append(field)

        return tuple(result)

    @staticmethod
    def _merge(
        *,
        deterministic: DocumentAnalysis,
        ai: DocumentAnalysis,
        allowed_ai_fields: tuple[DocumentField, ...],
    ) -> DocumentAnalysis:
        proposals = list(
            deterministic.proposals
        )

        for proposal in ai.proposals:
            if proposal.field not in allowed_ai_fields:
                continue

            proposals.append(proposal)

        return DocumentAnalysis(
            proposals=tuple(proposals)
        )
