import pytest

from src.multiai_v2.collaboration_planner import (
    CollaborationPlanner,
)
from src.multiai_v2.contracts import (
    CapabilityRequest,
    CollaborationExecutionPlan,
    CollaborationPlan,
    CollaborationRole,
    ExecutionPlan,
)


class FakeExecutionPlanner:
    def __init__(self) -> None:
        self.calls = []

    def plan(
        self,
        request,
        provider_health,
    ):
        self.calls.append(
            (request, provider_health)
        )

        return ExecutionPlan(
            capability_id=request.capability_id,
            capability_version=request.capability_version,
            provider_id="provider-a",
        )


def _role(
    role_id: str = "proposer",
    capability_id: str = "lesson.pedagogical_proposal",
) -> CollaborationRole:
    return CollaborationRole(
        role_id=role_id,
        capability_id=capability_id,
        capability_version="1.0",
    )


def _request(
    capability_id: str = "lesson.pedagogical_proposal",
) -> CapabilityRequest:
    return CapabilityRequest(
        capability_id=capability_id,
        capability_version="1.0",
        input_data={"topic": "fractions"},
    )


def test_collaboration_planner_creates_execution_plan_for_each_role():
    execution_planner = FakeExecutionPlanner()
    planner = CollaborationPlanner(
        execution_planner=execution_planner,
    )

    collaboration_plan = CollaborationPlan(
        collaboration_id="lesson-design",
        roles=(
            _role(),
            _role(
                role_id="verifier",
                capability_id="lesson.pedagogical_review",
            ),
        ),
    )

    role_requests = {
        "proposer": _request(),
        "verifier": _request(
            "lesson.pedagogical_review"
        ),
    }

    result = planner.plan(
        collaboration_plan=collaboration_plan,
        role_requests=role_requests,
        provider_health={},
    )

    assert result == (
        CollaborationExecutionPlan(
            collaboration_id="lesson-design",
            role_id="proposer",
            execution_plan=ExecutionPlan(
                capability_id="lesson.pedagogical_proposal",
                capability_version="1.0",
                provider_id="provider-a",
            ),
        ),
        CollaborationExecutionPlan(
            collaboration_id="lesson-design",
            role_id="verifier",
            execution_plan=ExecutionPlan(
                capability_id="lesson.pedagogical_review",
                capability_version="1.0",
                provider_id="provider-a",
            ),
        ),
    )


def test_collaboration_planner_passes_requests_to_execution_planner():
    execution_planner = FakeExecutionPlanner()
    planner = CollaborationPlanner(
        execution_planner=execution_planner,
    )

    request = _request()
    health = {}

    planner.plan(
        collaboration_plan=CollaborationPlan(
            collaboration_id="lesson-design",
            roles=(_role(),),
        ),
        role_requests={
            "proposer": request,
        },
        provider_health=health,
    )

    assert execution_planner.calls == [
        (request, health),
    ]


def test_missing_role_request_is_blocked():
    planner = CollaborationPlanner(
        execution_planner=FakeExecutionPlanner(),
    )

    with pytest.raises(ValueError):
        planner.plan(
            collaboration_plan=CollaborationPlan(
                collaboration_id="lesson-design",
                roles=(_role(),),
            ),
            role_requests={},
            provider_health={},
        )


def test_request_capability_must_match_role():
    planner = CollaborationPlanner(
        execution_planner=FakeExecutionPlanner(),
    )

    with pytest.raises(ValueError):
        planner.plan(
            collaboration_plan=CollaborationPlan(
                collaboration_id="lesson-design",
                roles=(_role(),),
            ),
            role_requests={
                "proposer": _request(
                    "lesson.pedagogical_review"
                ),
            },
            provider_health={},
        )


def test_request_version_must_match_role():
    planner = CollaborationPlanner(
        execution_planner=FakeExecutionPlanner(),
    )

    request = CapabilityRequest(
        capability_id="lesson.pedagogical_proposal",
        capability_version="2.0",
        input_data={},
    )

    with pytest.raises(ValueError):
        planner.plan(
            collaboration_plan=CollaborationPlan(
                collaboration_id="lesson-design",
                roles=(_role(),),
            ),
            role_requests={
                "proposer": request,
            },
            provider_health={},
        )


def test_returns_none_when_a_role_cannot_be_planned():
    class NoProviderExecutionPlanner:
        def plan(
            self,
            request,
            provider_health,
        ):
            return None

    planner = CollaborationPlanner(
        execution_planner=NoProviderExecutionPlanner(),
    )

    result = planner.plan(
        collaboration_plan=CollaborationPlan(
            collaboration_id="lesson-design",
            roles=(_role(),),
        ),
        role_requests={
            "proposer": _request(),
        },
        provider_health={},
    )

    assert result is None


def test_collaboration_planner_has_no_runtime_responsibility():
    forbidden = {
        "execute",
        "fallback",
        "accept",
        "reject",
        "validate",
        "register",
    }

    assert forbidden.isdisjoint(
        CollaborationPlanner.__dict__
    )