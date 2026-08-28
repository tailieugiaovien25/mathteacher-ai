from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, Sequence
from uuid import UUID

from assessment_generation_v2.services.canonical_assessment_selection_service import (
    CanonicalAssessmentSelection,
)


class BlueprintRequirementLinkError(ValueError):
    """Raised when canonical coverage cannot be persisted safely."""


@dataclass(frozen=True, slots=True)
class BlueprintRequirementAssignment:
    requirement_code: str
    coverage_role: str
    target_question_count: int
    sequence_number: int
    target_score: Decimal | None = None
    specification_note: str = ""

    def __post_init__(self) -> None:
        code = str(self.requirement_code).strip()
        role = str(self.coverage_role).strip().upper()
        count = int(self.target_question_count)
        sequence = int(self.sequence_number)
        note = str(self.specification_note).strip()

        if not code:
            raise BlueprintRequirementLinkError(
                "requirement_code is required"
            )
        if role not in {"PRIMARY", "SUPPORTING"}:
            raise BlueprintRequirementLinkError(
                "coverage_role must be PRIMARY or SUPPORTING"
            )
        if count <= 0:
            raise BlueprintRequirementLinkError(
                "target_question_count must be positive"
            )
        if sequence < 0:
            raise BlueprintRequirementLinkError(
                "sequence_number must not be negative"
            )

        score = self.target_score
        if score is not None:
            score = Decimal(str(score))
            if score <= 0:
                raise BlueprintRequirementLinkError(
                    "target_score must be positive"
                )

        object.__setattr__(self, "requirement_code", code)
        object.__setattr__(self, "coverage_role", role)
        object.__setattr__(self, "target_question_count", count)
        object.__setattr__(self, "sequence_number", sequence)
        object.__setattr__(self, "target_score", score)
        object.__setattr__(self, "specification_note", note)

    def as_rpc_record(self) -> dict[str, object]:
        return {
            "requirement_code": self.requirement_code,
            "coverage_role": self.coverage_role,
            "target_question_count": self.target_question_count,
            "target_score": (
                None
                if self.target_score is None
                else str(self.target_score)
            ),
            "sequence_number": self.sequence_number,
            "specification_note": self.specification_note,
        }


class BlueprintRequirementLinkGateway(Protocol):
    def replace_requirement_links(
        self,
        *,
        blueprint_version_id: str,
        assignments: Sequence[BlueprintRequirementAssignment],
    ) -> tuple[BlueprintRequirementAssignment, ...]:
        ...


class BlueprintRequirementLinkService:
    """Persist one finalized canonical selection as blueprint coverage."""

    def __init__(
        self,
        *,
        gateway: BlueprintRequirementLinkGateway,
    ) -> None:
        self._gateway = gateway

    def replace_from_selection(
        self,
        *,
        blueprint_version_id: str,
        selection: CanonicalAssessmentSelection,
        assignments: Sequence[BlueprintRequirementAssignment],
    ) -> tuple[BlueprintRequirementAssignment, ...]:
        try:
            normalized_blueprint_version_id = str(
                UUID(str(blueprint_version_id).strip())
            )
        except ValueError as error:
            raise BlueprintRequirementLinkError(
                "blueprint_version_id must be a valid UUID"
            ) from error

        if not selection.finalized:
            raise BlueprintRequirementLinkError(
                "canonical selection must be finalized"
            )

        rows = tuple(assignments)
        if not rows:
            raise BlueprintRequirementLinkError(
                "at least one requirement assignment is required"
            )

        selected_codes = tuple(selection.selected_requirement_codes)
        assignment_codes = tuple(row.requirement_code for row in rows)

        if len(set(assignment_codes)) != len(assignment_codes):
            raise BlueprintRequirementLinkError(
                "requirement assignments contain duplicate codes"
            )

        if set(assignment_codes) != set(selected_codes):
            raise BlueprintRequirementLinkError(
                "requirement assignments must exactly match "
                "the finalized canonical selection"
            )

        ordered = tuple(
            sorted(
                rows,
                key=lambda row: (
                    row.sequence_number,
                    row.requirement_code,
                ),
            )
        )

        return self._gateway.replace_requirement_links(
            blueprint_version_id=normalized_blueprint_version_id,
            assignments=ordered,
        )
