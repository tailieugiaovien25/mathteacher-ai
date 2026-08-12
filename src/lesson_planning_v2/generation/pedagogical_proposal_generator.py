from __future__ import annotations

from abc import ABC, abstractmethod

from lesson_planning_v2.proposals import (
    PedagogicalProposal,
    PedagogicalProposalRequest,
)


class PedagogicalProposalGenerator(ABC):
    """
    Domain-owned port for pedagogical proposal generation.

    Implementations may use AI, deterministic logic, or another
    generation mechanism. The lesson-planning domain does not know
    or select concrete providers.
    """

    @abstractmethod
    def generate(
        self,
        request: PedagogicalProposalRequest,
    ) -> PedagogicalProposal:
        raise NotImplementedError
