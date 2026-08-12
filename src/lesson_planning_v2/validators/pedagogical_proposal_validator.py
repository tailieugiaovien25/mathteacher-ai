from __future__ import annotations

from typing import Any

from core_v2.validation import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    Validator,
)
from lesson_planning_v2.proposals import PedagogicalProposal


class PedagogicalProposalValidator(Validator):
    """Validate pedagogical proposal structure before acceptance."""

    @property
    def data_type_id(self) -> str:
        return "PEDAGOGICAL_PROPOSAL"

    def validate(self, data: Any) -> ValidationResult:
        if not isinstance(data, PedagogicalProposal):
            return ValidationResult.from_issues(
                ValidationIssue(
                    code="PEDAGOGICAL_PROPOSAL_TYPE_INVALID",
                    message="data must be a PedagogicalProposal",
                    severity=ValidationSeverity.ERROR,
                )
            )

        issues: list[ValidationIssue] = []

        objective_ids = [item.objective_id for item in data.objectives]
        if len(objective_ids) != len(set(objective_ids)):
            issues.append(
                ValidationIssue(
                    code="PEDAGOGICAL_PROPOSAL_OBJECTIVE_ID_DUPLICATE",
                    message="objective IDs must be unique",
                    severity=ValidationSeverity.ERROR,
                    field="objectives",
                )
            )

        resource_ids = [item.resource_id for item in data.resources]
        if len(resource_ids) != len(set(resource_ids)):
            issues.append(
                ValidationIssue(
                    code="PEDAGOGICAL_PROPOSAL_RESOURCE_ID_DUPLICATE",
                    message="resource IDs must be unique",
                    severity=ValidationSeverity.ERROR,
                    field="resources",
                )
            )

        period_numbers = [item.period_in_lesson for item in data.periods]
        if len(period_numbers) != len(set(period_numbers)):
            issues.append(
                ValidationIssue(
                    code="PEDAGOGICAL_PROPOSAL_PERIOD_DUPLICATE",
                    message="period numbers must be unique",
                    severity=ValidationSeverity.ERROR,
                    field="periods",
                )
            )

        if not data.objectives and not data.resources and not data.periods:
            issues.append(
                ValidationIssue(
                    code="PEDAGOGICAL_PROPOSAL_EMPTY",
                    message="proposal contains no pedagogical content",
                    severity=ValidationSeverity.WARNING,
                )
            )

        return ValidationResult(issues=tuple(issues))


def get_pedagogical_proposal_validator() -> PedagogicalProposalValidator:
    return PedagogicalProposalValidator()
