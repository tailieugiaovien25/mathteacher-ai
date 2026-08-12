from __future__ import annotations

from dataclasses import dataclass

from lesson_planning_v2.models import (
    LessonObjective,
    PeriodPlan,
    TeachingResource,
)
from lesson_planning_v2.provenance import ProposalProvenance


@dataclass(frozen=True)
class PedagogicalProposal:
    """
    AI/provider-neutral pedagogical proposal.

    Deliberately excludes canonical authority and domain identity fields.
    It may propose pedagogical content only.
    """

    objectives: tuple[LessonObjective, ...] = ()
    resources: tuple[TeachingResource, ...] = ()
    periods: tuple[PeriodPlan, ...] = ()

    provider_id: str | None = None
    proposal_id: str | None = None
    provenance: ProposalProvenance | None = None
