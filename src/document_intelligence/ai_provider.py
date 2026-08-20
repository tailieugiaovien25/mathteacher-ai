from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from document_intelligence.contracts import (
    AnalysisSource,
    DocumentAnalysis,
    DocumentField,
    DocumentFieldProposal,
)


@dataclass(frozen=True)
class AIFieldCandidate:
    field: DocumentField
    value: str
    confidence: float
    evidence: str = ""

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError(
                "AI candidate value must not be empty"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )


class AIDocumentProvider(Protocol):
    """
    Provider-independent AI boundary.

    Implementations may call OpenAI, Gemini, or another
    provider, but must return structured candidates only.
    """

    def analyze(
        self,
        *,
        document_text: str,
    ) -> tuple[AIFieldCandidate, ...]:
        ...


class AIDocumentAnalyzer:
    """
    Converts provider candidates into the canonical
    DocumentAnalysis contract.

    This class never modifies the source document.
    """

    def __init__(
        self,
        *,
        provider: AIDocumentProvider,
    ) -> None:
        self._provider = provider

    def analyze(
        self,
        *,
        document_text: str,
    ) -> DocumentAnalysis:
        candidates = self._provider.analyze(
            document_text=document_text
        )

        proposals = tuple(
            DocumentFieldProposal(
                field=candidate.field,
                value=candidate.value,
                confidence=candidate.confidence,
                source=AnalysisSource.AI,
                evidence=candidate.evidence,
            )
            for candidate in candidates
        )

        return DocumentAnalysis(
            proposals=proposals
        )
