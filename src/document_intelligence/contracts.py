from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class DocumentField(str, Enum):
    DRAFTING_DATE = "drafting_date"
    TEACHING_DATE = "teaching_date"
    CLASS_NAME = "class_name"
    CURRICULUM_PERIOD = "curriculum_period"
    LESSON_TITLE = "lesson_title"


class AnalysisSource(str, Enum):
    DETERMINISTIC = "deterministic"
    AI = "ai"


@dataclass(frozen=True)
class DocumentFieldProposal:
    field: DocumentField
    value: str
    confidence: float
    source: AnalysisSource
    evidence: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

        if not self.value.strip():
            raise ValueError(
                "proposal value must not be empty"
            )


@dataclass(frozen=True)
class DocumentAnalysis:
    proposals: tuple[DocumentFieldProposal, ...] = ()

    def for_field(
        self,
        field: DocumentField,
    ) -> tuple[DocumentFieldProposal, ...]:
        return tuple(
            proposal
            for proposal in self.proposals
            if proposal.field == field
        )


class DocumentAnalyzer(Protocol):
    def analyze(
        self,
        *,
        document_text: str,
    ) -> DocumentAnalysis:
        """
        Analyze document content without modifying the
        source document.

        Implementations may be deterministic or AI-backed.
        """
        ...
