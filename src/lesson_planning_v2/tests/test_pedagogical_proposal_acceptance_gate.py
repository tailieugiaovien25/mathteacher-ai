import pytest

from core_v2.validation import ValidationSeverity
from lesson_planning_v2.acceptance import (
    PedagogicalProposalAcceptancePolicy,
    ProposalAcceptanceStatus,
)
from lesson_planning_v2.adapters import LessonPlanDraftAdapter
from lesson_planning_v2.models import (
    LessonObjective,
    PeriodPlan,
    TeachingResource,
)
from lesson_planning_v2.proposals import PedagogicalProposal
from lesson_planning_v2.validators import PedagogicalProposalValidator


def make_proposal() -> PedagogicalProposal:
    return PedagogicalProposal(
        objectives=(
            LessonObjective(
                objective_id="OBJ-001",
                objective_type="KNOWLEDGE",
                statement="Hoc sinh thuc hien duoc nhiem vu hoc tap.",
            ),
        ),
        resources=(
            TeachingResource(
                resource_id="RES-001",
                name="Phieu hoc tap",
                resource_type="WORKSHEET",
            ),
        ),
        periods=(PeriodPlan(period_in_lesson=1),),
        provider_id="AI-PROVIDER-TEST",
        proposal_id="PROP-001",
    )


def test_validator_uses_core_validation_result():
    result = PedagogicalProposalValidator().validate(make_proposal())

    assert result.is_valid
    assert result.issues == ()


def test_validator_rejects_wrong_data_type():
    result = PedagogicalProposalValidator().validate({})

    assert not result.is_valid
    assert result.issues[0].code == "PEDAGOGICAL_PROPOSAL_TYPE_INVALID"


def test_validator_detects_duplicate_objective_ids():
    objective = LessonObjective(
        objective_id="OBJ-001",
        objective_type="KNOWLEDGE",
        statement="Muc tieu",
    )
    proposal = PedagogicalProposal(objectives=(objective, objective))

    result = PedagogicalProposalValidator().validate(proposal)

    assert not result.is_valid
    assert any(
        issue.code == "PEDAGOGICAL_PROPOSAL_OBJECTIVE_ID_DUPLICATE"
        for issue in result.issues
    )


def test_validator_detects_duplicate_resource_ids():
    resource = TeachingResource(
        resource_id="RES-001",
        name="Tai nguyen",
        resource_type="WORKSHEET",
    )
    proposal = PedagogicalProposal(resources=(resource, resource))

    result = PedagogicalProposalValidator().validate(proposal)

    assert not result.is_valid


def test_validator_detects_duplicate_periods():
    proposal = PedagogicalProposal(
        periods=(PeriodPlan(1), PeriodPlan(1)),
    )

    result = PedagogicalProposalValidator().validate(proposal)

    assert not result.is_valid


def test_empty_proposal_is_warning_not_error():
    result = PedagogicalProposalValidator().validate(
        PedagogicalProposal()
    )

    assert result.is_valid
    assert result.has_warnings
    assert result.issues[0].severity is ValidationSeverity.WARNING


def test_acceptance_policy_accepts_valid_proposal():
    proposal = make_proposal()
    validation = PedagogicalProposalValidator().validate(proposal)

    decision = PedagogicalProposalAcceptancePolicy().decide(
        proposal=proposal,
        validation_result=validation,
    )

    assert decision.status is ProposalAcceptanceStatus.ACCEPTED
    assert decision.is_accepted
    assert decision.proposal is proposal


def test_acceptance_policy_allows_warning_without_error():
    proposal = PedagogicalProposal()
    validation = PedagogicalProposalValidator().validate(proposal)

    decision = PedagogicalProposalAcceptancePolicy().decide(
        proposal=proposal,
        validation_result=validation,
    )

    assert decision.is_accepted
    assert decision.validation_result.has_warnings


def test_acceptance_policy_rejects_validation_errors():
    objective = LessonObjective(
        objective_id="OBJ-001",
        objective_type="KNOWLEDGE",
        statement="Muc tieu",
    )
    proposal = PedagogicalProposal(objectives=(objective, objective))
    validation = PedagogicalProposalValidator().validate(proposal)

    decision = PedagogicalProposalAcceptancePolicy().decide(
        proposal=proposal,
        validation_result=validation,
    )

    assert decision.status is ProposalAcceptanceStatus.REJECTED
    assert not decision.is_accepted
    assert decision.proposal is None


def test_adapter_converts_accepted_proposal_to_draft():
    proposal = make_proposal()
    validation = PedagogicalProposalValidator().validate(proposal)
    decision = PedagogicalProposalAcceptancePolicy().decide(
        proposal=proposal,
        validation_result=validation,
    )

    draft = LessonPlanDraftAdapter().adapt(decision)

    assert draft.objectives == proposal.objectives
    assert draft.resources == proposal.resources
    assert draft.periods == proposal.periods


def test_adapter_blocks_rejected_proposal():
    objective = LessonObjective(
        objective_id="OBJ-001",
        objective_type="KNOWLEDGE",
        statement="Muc tieu",
    )
    proposal = PedagogicalProposal(objectives=(objective, objective))
    validation = PedagogicalProposalValidator().validate(proposal)
    decision = PedagogicalProposalAcceptancePolicy().decide(
        proposal=proposal,
        validation_result=validation,
    )

    with pytest.raises(ValueError, match="accepted"):
        LessonPlanDraftAdapter().adapt(decision)


def test_adapter_cannot_receive_raw_proposal():
    with pytest.raises((AttributeError, TypeError)):
        LessonPlanDraftAdapter().adapt(make_proposal())


def test_validator_data_type_id_is_stable():
    assert (
        PedagogicalProposalValidator().data_type_id
        == "PEDAGOGICAL_PROPOSAL"
    )
