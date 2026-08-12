from __future__ import annotations

from dataclasses import dataclass

from lesson_planning_v2.contexts import LessonPlanningContext


@dataclass(frozen=True)
class PedagogicalProposalRequest:
    """
    Domain-owned request for pedagogical proposal generation.

    Trusted canonical/domain context remains authoritative. This contract
    gives an AI/provider context to reason from; it does not transfer
    canonical authority to that provider.
    """

    context: LessonPlanningContext
    proposal_scope: str = "FULL_LESSON"
    period_in_lesson: int | None = None
    instructions: str | None = None

    def __post_init__(self) -> None:
        scope = self.proposal_scope.strip()
        if not scope:
            raise ValueError("proposal_scope must not be empty")

        if self.period_in_lesson is not None:
            if self.period_in_lesson <= 0:
                raise ValueError(
                    "period_in_lesson must be greater than zero"
                )
            if self.period_in_lesson > self.context.periods:
                raise ValueError(
                    "period_in_lesson must not exceed context periods"
                )

        object.__setattr__(self, "proposal_scope", scope)
