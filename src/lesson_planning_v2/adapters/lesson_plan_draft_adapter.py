from __future__ import annotations

from dataclasses import asdict

from lesson_planning_v2.acceptance import ProposalAcceptanceDecision
from lesson_planning_v2.builders import LessonPlanDraft


PROPOSAL_PROVENANCE_METADATA_KEY = "proposal_provenance"


class LessonPlanDraftAdapter:
    """Convert only an accepted proposal into a LessonPlanDraft."""

    def adapt(
        self,
        decision: ProposalAcceptanceDecision,
        *,
        plan_mode: str = "FULL_LESSON",
        period_in_lesson: int | None = None,
        status: str = "DRAFT",
    ) -> LessonPlanDraft:
        if not decision.is_accepted or decision.proposal is None:
            raise ValueError(
                "pedagogical proposal must be accepted before draft conversion"
            )

        proposal = decision.proposal
        metadata: dict[str, object] = {}

        if proposal.provenance is not None:
            metadata[PROPOSAL_PROVENANCE_METADATA_KEY] = asdict(
                proposal.provenance
            )

        return LessonPlanDraft(
            plan_mode=plan_mode,
            period_in_lesson=period_in_lesson,
            objectives=proposal.objectives,
            resources=proposal.resources,
            periods=proposal.periods,
            status=status,
            metadata=metadata,
        )
