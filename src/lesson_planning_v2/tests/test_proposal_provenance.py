from dataclasses import fields

from curriculum_v2.canonical_curriculum import get_canonical_curriculum
from educational_planning_v2 import EducationalPlanningFacade
from educational_planning_v2.builders import PlanItemDraft
from lesson_planning_v2.acceptance import (
    PedagogicalProposalAcceptancePolicy,
)
from lesson_planning_v2.adapters import (
    LessonPlanDraftAdapter,
    PROPOSAL_PROVENANCE_METADATA_KEY,
)
from lesson_planning_v2.builders import LessonPlanBuilder
from lesson_planning_v2.proposals import PedagogicalProposal
from lesson_planning_v2.provenance import ProposalProvenance
from lesson_planning_v2.services.lesson_planning_context_service import (
    LessonPlanningContextService,
)
from lesson_planning_v2.validators import PedagogicalProposalValidator


FORBIDDEN_AUTHORITY_FIELDS = {
    "educational_plan_id",
    "plan_item_id",
    "grade",
    "curriculum_ref",
    "curriculum_node_refs",
    "canonical_requirement_refs",
    "total_periods",
}


def make_provenance() -> ProposalProvenance:
    return ProposalProvenance(
        proposal_id="PROP-TRACE-001",
        provider_id="AI-PROVIDER-001",
        request_id="REQ-001",
        execution_id="EXEC-001",
        trace_id="TRACE-001",
    )


def make_context():
    curriculum = get_canonical_curriculum()
    requirement = curriculum.requirement_by_id("YCCD-MATH-06-0001")
    assert requirement is not None

    plan = EducationalPlanningFacade().build_plan(
        educational_plan_id="EDU-PLAN-MATH-G6-TRACE-001",
        academic_year="2026-2027",
        subject="MATHEMATICS",
        grade=6,
        curriculum_ref="CTGDPT-2018-MATH",
        item_drafts=(
            PlanItemDraft(
                title="Bai hoc traceability",
                periods=1,
                curriculum_node_ids=(
                    requirement.curriculum_node_ref,
                ),
                canonical_requirement_ids=(
                    requirement.canonical_id,
                ),
            ),
        ),
    )

    return LessonPlanningContextService().build(
        plan,
        plan.items[0],
    )


def accepted_decision(proposal: PedagogicalProposal):
    validation = PedagogicalProposalValidator().validate(proposal)
    assert validation.is_valid
    return PedagogicalProposalAcceptancePolicy().decide(
        proposal=proposal,
        validation_result=validation,
    )


def test_provenance_contains_trace_identity():
    provenance = make_provenance()

    assert provenance.proposal_id == "PROP-TRACE-001"
    assert provenance.provider_id == "AI-PROVIDER-001"
    assert provenance.execution_id == "EXEC-001"
    assert provenance.trace_id == "TRACE-001"


def test_provenance_excludes_canonical_authority():
    names = {item.name for item in fields(ProposalProvenance)}

    assert names.isdisjoint(FORBIDDEN_AUTHORITY_FIELDS)


def test_proposal_can_carry_structured_provenance():
    provenance = make_provenance()
    proposal = PedagogicalProposal(provenance=provenance)

    assert proposal.provenance is provenance


def test_acceptance_decision_preserves_proposal_provenance():
    provenance = make_provenance()
    proposal = PedagogicalProposal(provenance=provenance)

    decision = accepted_decision(proposal)

    assert decision.is_accepted
    assert decision.proposal is proposal
    assert decision.proposal.provenance is provenance


def test_adapter_copies_provenance_into_draft_metadata():
    provenance = make_provenance()
    proposal = PedagogicalProposal(provenance=provenance)

    draft = LessonPlanDraftAdapter().adapt(
        accepted_decision(proposal)
    )

    stored = draft.metadata[PROPOSAL_PROVENANCE_METADATA_KEY]
    assert stored["proposal_id"] == provenance.proposal_id
    assert stored["provider_id"] == provenance.provider_id
    assert stored["execution_id"] == provenance.execution_id
    assert stored["trace_id"] == provenance.trace_id


def test_adapter_does_not_create_provenance_when_absent():
    draft = LessonPlanDraftAdapter().adapt(
        accepted_decision(PedagogicalProposal())
    )

    assert PROPOSAL_PROVENANCE_METADATA_KEY not in draft.metadata


def test_builder_preserves_draft_metadata_in_lesson_plan():
    provenance = make_provenance()
    proposal = PedagogicalProposal(provenance=provenance)
    draft = LessonPlanDraftAdapter().adapt(
        accepted_decision(proposal)
    )

    plan = LessonPlanBuilder().build(
        lesson_plan_id="LESSON-TRACE-001",
        context=make_context(),
        draft=draft,
    )

    assert (
        plan.metadata[PROPOSAL_PROVENANCE_METADATA_KEY]["trace_id"]
        == "TRACE-001"
    )


def test_metadata_cannot_override_context_authority():
    context = make_context()
    proposal = PedagogicalProposal(provenance=make_provenance())
    draft = LessonPlanDraftAdapter().adapt(
        accepted_decision(proposal)
    )

    draft.metadata.update(
        {
            "grade": 9,
            "curriculum_ref": "FAKE-CURRICULUM",
            "educational_plan_id": "FAKE-PLAN",
            "plan_item_id": "FAKE-ITEM",
            "canonical_requirement_refs": ("FAKE-YCCD",),
        }
    )

    plan = LessonPlanBuilder().build(
        lesson_plan_id="LESSON-TRACE-002",
        context=context,
        draft=draft,
    )

    assert plan.grade == context.grade
    assert plan.curriculum_ref == context.curriculum_scope.curriculum_ref
    assert plan.educational_plan_id == context.educational_plan_id
    assert plan.plan_item_id == context.plan_item_id
    assert plan.canonical_requirement_refs == tuple(
        requirement.canonical_id
        for requirement in context.requirements
    )


def test_builder_copies_metadata_mapping():
    proposal = PedagogicalProposal(provenance=make_provenance())
    draft = LessonPlanDraftAdapter().adapt(
        accepted_decision(proposal)
    )

    plan = LessonPlanBuilder().build(
        lesson_plan_id="LESSON-TRACE-003",
        context=make_context(),
        draft=draft,
    )

    assert plan.metadata == draft.metadata
    assert plan.metadata is not draft.metadata
