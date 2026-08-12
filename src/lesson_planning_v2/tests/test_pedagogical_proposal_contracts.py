from dataclasses import FrozenInstanceError, fields

import pytest

from curriculum_v2.canonical_curriculum import get_canonical_curriculum
from educational_planning_v2.builders import PlanItemDraft
from educational_planning_v2 import EducationalPlanningFacade
from lesson_planning_v2.services.lesson_planning_context_service import (
    LessonPlanningContextService,
)


from lesson_planning_v2.models import (
    LearningActivity,
    LessonObjective,
    PeriodPlan,
    TeachingResource,
)
from lesson_planning_v2.proposals import (
    PedagogicalProposal,
    PedagogicalProposalRequest,
)


FORBIDDEN_AUTHORITY_FIELDS = {
    "educational_plan_id",
    "plan_item_id",
    "grade",
    "curriculum_ref",
    "curriculum_node_refs",
    "canonical_requirement_refs",
    "total_periods",
}


def make_context():
    curriculum = get_canonical_curriculum()
    requirement = curriculum.requirement_by_id("YCCD-MATH-06-0001")
    assert requirement is not None

    plan = EducationalPlanningFacade().build_plan(
        educational_plan_id="EDU-PLAN-MATH-G6-PROP-001",
        academic_year="2026-2027",
        subject="MATHEMATICS",
        grade=6,
        curriculum_ref="CTGDPT-2018-MATH",
        item_drafts=(
            PlanItemDraft(
                title="Bai hoc proposal contract",
                periods=2,
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


def test_request_carries_trusted_lesson_planning_context():
    context = make_context()
    request = PedagogicalProposalRequest(context=context)

    assert request.context is context
    assert request.context.grade == 6
    assert request.context.requirements[0].canonical_id == (
        "YCCD-MATH-06-0001"
    )


def test_request_normalizes_proposal_scope():
    request = PedagogicalProposalRequest(
        context=make_context(),
        proposal_scope="  FULL_LESSON  ",
    )

    assert request.proposal_scope == "FULL_LESSON"


def test_request_rejects_empty_proposal_scope():
    with pytest.raises(ValueError, match="proposal_scope"):
        PedagogicalProposalRequest(
            context=make_context(),
            proposal_scope="   ",
        )


def test_request_rejects_invalid_period():
    with pytest.raises(ValueError, match="greater than zero"):
        PedagogicalProposalRequest(
            context=make_context(),
            period_in_lesson=0,
        )


def test_request_rejects_period_outside_trusted_context():
    with pytest.raises(ValueError, match="context periods"):
        PedagogicalProposalRequest(
            context=make_context(),
            period_in_lesson=3,
        )


def test_proposal_accepts_pedagogical_content():
    objective = LessonObjective(
        objective_id="OBJ-001",
        objective_type="KNOWLEDGE",
        statement="Hoc sinh thuc hien duoc nhiem vu hoc tap.",
        source_requirement_refs=("YCCD-MATH-06-0001",),
    )
    resource = TeachingResource(
        resource_id="RES-001",
        name="Phieu hoc tap",
        resource_type="WORKSHEET",
    )
    activity = LearningActivity(
        activity_id="ACT-001",
        title="Kham pha",
        activity_type="DISCOVERY",
        order=1,
        objective_refs=("OBJ-001",),
    )
    period = PeriodPlan(
        period_in_lesson=1,
        activities=(activity,),
    )

    proposal = PedagogicalProposal(
        objectives=(objective,),
        resources=(resource,),
        periods=(period,),
        provider_id="AI-PROVIDER-TEST",
        proposal_id="PROP-001",
    )

    assert proposal.objectives == (objective,)
    assert proposal.resources == (resource,)
    assert proposal.periods == (period,)
    assert proposal.provider_id == "AI-PROVIDER-TEST"


def test_proposal_contract_excludes_canonical_authority_fields():
    proposal_fields = {
        field.name for field in fields(PedagogicalProposal)
    }

    assert proposal_fields.isdisjoint(FORBIDDEN_AUTHORITY_FIELDS)


def test_request_does_not_duplicate_canonical_authority_fields():
    request_fields = {
        field.name for field in fields(PedagogicalProposalRequest)
    }

    assert request_fields.isdisjoint(FORBIDDEN_AUTHORITY_FIELDS)
    assert "context" in request_fields


def test_proposal_is_immutable():
    proposal = PedagogicalProposal()

    with pytest.raises(FrozenInstanceError):
        proposal.provider_id = "OTHER"


def test_request_is_immutable():
    request = PedagogicalProposalRequest(
        context=make_context(),
    )

    with pytest.raises(FrozenInstanceError):
        request.proposal_scope = "OTHER"


def test_public_proposal_imports_work():
    assert PedagogicalProposal.__name__ == "PedagogicalProposal"
    assert (
        PedagogicalProposalRequest.__name__
        == "PedagogicalProposalRequest"
    )

