import pytest

from src.multiai_v2.contracts import ExecutionPlan


def test_execution_plan_can_be_created():
    plan = ExecutionPlan(
        capability_id="lesson.pedagogical_proposal",
        capability_version="1.0",
        provider_id="provider-a",
    )

    assert plan.capability_id == "lesson.pedagogical_proposal"
    assert plan.capability_version == "1.0"
    assert plan.provider_id == "provider-a"


def test_execution_plan_identity_is_normalized():
    plan = ExecutionPlan(
        capability_id="  lesson.pedagogical_proposal  ",
        capability_version="  1.0  ",
        provider_id="  provider-a  ",
    )

    assert plan.capability_id == "lesson.pedagogical_proposal"
    assert plan.capability_version == "1.0"
    assert plan.provider_id == "provider-a"


@pytest.mark.parametrize(
    ("capability_id", "capability_version", "provider_id"),
    [
        ("", "1.0", "provider-a"),
        ("   ", "1.0", "provider-a"),
        ("lesson.pedagogical_proposal", "", "provider-a"),
        ("lesson.pedagogical_proposal", "   ", "provider-a"),
        ("lesson.pedagogical_proposal", "1.0", ""),
        ("lesson.pedagogical_proposal", "1.0", "   "),
    ],
)
def test_execution_plan_requires_non_empty_identity(
    capability_id: str,
    capability_version: str,
    provider_id: str,
):
    with pytest.raises(ValueError):
        ExecutionPlan(
            capability_id=capability_id,
            capability_version=capability_version,
            provider_id=provider_id,
        )


def test_execution_plan_is_immutable():
    plan = ExecutionPlan(
        capability_id="lesson.pedagogical_proposal",
        capability_version="1.0",
        provider_id="provider-a",
    )

    with pytest.raises(AttributeError):
        plan.provider_id = "provider-b"


def test_execution_plan_has_no_execution_or_acceptance_responsibility():
    forbidden = {
        "execute",
        "fallback",
        "validate",
        "accept",
        "reject",
        "select_provider",
        "rank_provider",
    }

    assert forbidden.isdisjoint(ExecutionPlan.__dict__)