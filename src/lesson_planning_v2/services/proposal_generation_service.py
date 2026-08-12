from __future__ import annotations

from lesson_planning_v2.acceptance import (
    PedagogicalProposalAcceptancePolicy,
    ProposalAcceptanceDecision,
)
from lesson_planning_v2.generation import (
    PedagogicalProposalGenerator,
)
from lesson_planning_v2.proposals import (
    PedagogicalProposalRequest,
)
from lesson_planning_v2.validators import (
    PedagogicalProposalValidator,
)


class ProposalGenerationService:
    """
    Orchestrate pedagogical proposal generation and acceptance.

    Generation proposes pedagogical content.
    Validation evaluates the generated proposal.
    Acceptance remains owned by the acceptance policy.
    """

    def __init__(
        self,
        *,
        generator: PedagogicalProposalGenerator,
        validator: PedagogicalProposalValidator | None = None,
        acceptance_policy: PedagogicalProposalAcceptancePolicy | None = None,
    ) -> None:
        self._generator = generator
        self._validator = validator or PedagogicalProposalValidator()
        self._acceptance_policy = (
            acceptance_policy
            or PedagogicalProposalAcceptancePolicy()
        )

    def generate(
        self,
        request: PedagogicalProposalRequest,
    ) -> ProposalAcceptanceDecision:
        proposal = self._generator.generate(request)

        validation_result = self._validator.validate(
            proposal
        )

        return self._acceptance_policy.decide(
            proposal=proposal,
            validation_result=validation_result,
        )
