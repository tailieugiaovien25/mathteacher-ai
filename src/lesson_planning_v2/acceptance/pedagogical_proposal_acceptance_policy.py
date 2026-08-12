from __future__ import annotations

from core_v2.validation import ValidationResult
from lesson_planning_v2.proposals import PedagogicalProposal
from lesson_planning_v2.acceptance.proposal_acceptance_decision import (
    ProposalAcceptanceDecision,
    ProposalAcceptanceStatus,
)


class PedagogicalProposalAcceptancePolicy:
    """Accept valid proposals; warnings alone do not force rejection."""

    def decide(
        self,
        *,
        proposal: PedagogicalProposal,
        validation_result: ValidationResult,
    ) -> ProposalAcceptanceDecision:
        if validation_result.has_errors:
            return ProposalAcceptanceDecision(
                status=ProposalAcceptanceStatus.REJECTED,
                proposal=None,
                validation_result=validation_result,
                reason="proposal validation contains errors",
            )

        return ProposalAcceptanceDecision(
            status=ProposalAcceptanceStatus.ACCEPTED,
            proposal=proposal,
            validation_result=validation_result,
        )
