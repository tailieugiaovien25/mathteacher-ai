from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from document_intelligence.contracts import (
    DocumentAnalysis,
    DocumentField,
    DocumentFieldProposal,
)


class ValidationStatus(str, Enum):
    ACCEPTED = "accepted"
    CONFLICT = "conflict"
    UNVERIFIED = "unverified"


@dataclass(frozen=True)
class CanonicalDocumentContext:
    class_name: str | None = None
    curriculum_period: int | None = None
    lesson_title: str | None = None
    drafting_date: str | None = None
    teaching_date: str | None = None

    def value_for(
        self,
        field: DocumentField,
    ) -> str | None:
        mapping = {
            DocumentField.CLASS_NAME: self.class_name,
            DocumentField.CURRICULUM_PERIOD: (
                str(self.curriculum_period)
                if self.curriculum_period is not None
                else None
            ),
            DocumentField.LESSON_TITLE: self.lesson_title,
            DocumentField.DRAFTING_DATE: self.drafting_date,
            DocumentField.TEACHING_DATE: self.teaching_date,
        }

        return mapping[field]


@dataclass(frozen=True)
class ValidatedDocumentProposal:
    proposal: DocumentFieldProposal
    status: ValidationStatus
    canonical_value: str | None = None


@dataclass(frozen=True)
class ValidatedDocumentAnalysis:
    proposals: tuple[
        ValidatedDocumentProposal,
        ...
    ]


class DocumentAnalysisValidator:
    def validate(
        self,
        *,
        analysis: DocumentAnalysis,
        canonical: CanonicalDocumentContext,
    ) -> ValidatedDocumentAnalysis:
        validated = []

        for proposal in analysis.proposals:
            canonical_value = canonical.value_for(
                proposal.field
            )

            if canonical_value is None:
                status = ValidationStatus.UNVERIFIED

            elif (
                self._normalize(canonical_value)
                == self._normalize(proposal.value)
            ):
                status = ValidationStatus.ACCEPTED

            else:
                status = ValidationStatus.CONFLICT

            validated.append(
                ValidatedDocumentProposal(
                    proposal=proposal,
                    status=status,
                    canonical_value=canonical_value,
                )
            )

        return ValidatedDocumentAnalysis(
            proposals=tuple(validated)
        )

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        return " ".join(
            value.strip().casefold().split()
        )
