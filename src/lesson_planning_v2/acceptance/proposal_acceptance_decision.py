from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core_v2.validation import ValidationResult
from lesson_planning_v2.proposals import PedagogicalProposal


class ProposalAcceptanceStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class ProposalAcceptanceDecision:
    status: ProposalAcceptanceStatus
    proposal: PedagogicalProposal | None
    validation_result: ValidationResult
    reason: str | None = None

    @property
    def is_accepted(self) -> bool:
        return self.status is ProposalAcceptanceStatus.ACCEPTED
