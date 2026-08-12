import pytest

from src.multiai_v2.contracts import (
    CollaborationExecutionPlan,
    ExecutionPlan,
)


def _execution_plan(
    provider_id: str = "provider-a",
) -> ExecutionPlan:
    return ExecutionPlan(
        capability_id="lesson.pedagogical_proposal",
        capability_version="1.0",
        provider_id=provider_id,
    )


def test_collaboration_execution_plan_can_be_created():
    plan = CollaborationExecutionPlan(
        collaboration_id="lesson-review",
        role_id="proposer",
        execution_plan=_execution_plan(),
    )

    assert plan.collaboration_id == "lesson-review"
    assert plan.role_id == "proposer"
    assert plan.execution_plan == _execution_plan()


def test_collaboration_execution_plan_normalizes_identity_fields():
    plan = CollaborationExecutionPlan(
        collaboration_id="  lesson-review  ",
        role_id="  proposer  ",
        execution_plan=_execution_plan(),
    )

    assert plan.collaboration_id == "lesson-review"
    assert plan.role_id == "proposer"


@pytest.mark.parametrize(
    "collaboration_id",
    [
        "",
        "   ",
    ],
)
def test_empty_collaboration_id_is_blocked(
    collaboration_id,
):
    with pytest.raises(ValueError):
        CollaborationExecutionPlan(
            collaboration_id=collaboration_id,
            role_id="proposer",
            execution_plan=_execution_plan(),
        )


@pytest.mark.parametrize(
    "role_id",
    [
        "",
        "   ",
    ],
)
def test_empty_role_id_is_blocked(role_id):
    with pytest.raises(ValueError):
        CollaborationExecutionPlan(
            collaboration_id="lesson-review",
            role_id=role_id,
            execution_plan=_execution_plan(),
        )


def test_execution_plan_must_be_execution_plan():
    with pytest.raises(TypeError):
        CollaborationExecutionPlan(
            collaboration_id="lesson-review",
            role_id="proposer",
            execution_plan="not-an-execution-plan",
        )


def test_collaboration_execution_plan_is_immutable():
    plan = CollaborationExecutionPlan(
        collaboration_id="lesson-review",
        role_id="proposer",
        execution_plan=_execution_plan(),
    )

    with pytest.raises(Exception):
        plan.role_id = "verifier"


def test_collaboration_execution_plan_has_no_runtime_responsibility():
    forbidden = {
        "execute",
        "select",
        "route",
        "fallback",
        "validate",
        "accept",
        "reject",
        "register",
    }

    assert forbidden.isdisjoint(
        CollaborationExecutionPlan.__dict__
    )