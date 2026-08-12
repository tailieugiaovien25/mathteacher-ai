from lesson_planning_v2.generation import (
    PedagogicalProposalGenerator,
)
from lesson_planning_v2.proposals import (
    PedagogicalProposal,
)


def test_generator_is_abstract():
    try:
        PedagogicalProposalGenerator()
    except TypeError:
        pass
    else:
        raise AssertionError(
            "PedagogicalProposalGenerator must remain abstract"
        )


def test_generator_contract_exposes_generate():
    assert hasattr(
        PedagogicalProposalGenerator,
        "generate",
    )


def test_generator_contract_does_not_expose_provider_selection():
    forbidden = {
        "provider_id",
        "model_id",
        "route",
        "select_provider",
    }

    assert forbidden.isdisjoint(
        PedagogicalProposalGenerator.__dict__
    )


def test_pedagogical_proposal_remains_generation_output():
    assert PedagogicalProposal is not None
