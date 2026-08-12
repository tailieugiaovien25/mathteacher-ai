from lesson_planning_v2.acceptance import (
    ProposalAcceptanceStatus,
)
from lesson_planning_v2.generation import (
    PedagogicalProposalGenerator,
)
from lesson_planning_v2.models import (
    LessonObjective,
)
from lesson_planning_v2.proposals import (
    PedagogicalProposal,
)
from lesson_planning_v2.services import (
    ProposalGenerationService,
)


class StubGenerator(PedagogicalProposalGenerator):
    def __init__(self, proposal):
        self.proposal = proposal
        self.received_request = None

    def generate(self, request):
        self.received_request = request
        return self.proposal


def test_service_is_publicly_exported():
    assert ProposalGenerationService is not None


def test_service_passes_request_to_generator():
    proposal = PedagogicalProposal()
    generator = StubGenerator(proposal)
    service = ProposalGenerationService(generator=generator)

    request = object()

    service.generate(request)

    assert generator.received_request is request


def test_service_accepts_valid_generated_proposal():
    proposal = PedagogicalProposal(
        objectives=(
            LessonObjective(
                objective_id="OBJ-001",
                objective_type="KNOWLEDGE",
                statement="Muc tieu hoc tap.",
            ),
        ),
    )

    decision = ProposalGenerationService(
        generator=StubGenerator(proposal)
    ).generate(object())

    assert decision.status is ProposalAcceptanceStatus.ACCEPTED
    assert decision.proposal is proposal


def test_service_rejects_invalid_generated_proposal():
    objective = LessonObjective(
        objective_id="OBJ-001",
        objective_type="KNOWLEDGE",
        statement="Muc tieu hoc tap.",
    )

    proposal = PedagogicalProposal(
        objectives=(objective, objective),
    )

    decision = ProposalGenerationService(
        generator=StubGenerator(proposal)
    ).generate(object())

    assert decision.status is ProposalAcceptanceStatus.REJECTED
    assert decision.proposal is None
    assert decision.validation_result.has_errors


def test_service_does_not_build_lesson_plan():
    forbidden = {
        "build",
        "build_lesson_plan",
        "select_provider",
        "route",
    }

    assert forbidden.isdisjoint(
        ProposalGenerationService.__dict__
    )
