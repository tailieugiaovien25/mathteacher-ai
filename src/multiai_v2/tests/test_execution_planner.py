import pytest

from src.multiai_v2.contracts import (
    CapabilityRequest,
    ExecutionPlan,
    ProviderCapability,
    ProviderHealth,
    ProviderStatus,
)
from src.multiai_v2.execution_planner import ExecutionPlanner
from src.multiai_v2.provider_registry import ProviderRegistry


class FakeProvider:
    def __init__(self, provider_id: str) -> None:
        self._provider_id = provider_id

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def capabilities(self) -> tuple[ProviderCapability, ...]:
        return (
            ProviderCapability(
                capability_id="lesson.pedagogical_proposal",
                version="1.0",
            ),
        )

    def execute(self, request):
        raise AssertionError(
            "ExecutionPlanner must not execute providers"
        )


class FakeRoutingPolicy:
    def __init__(self, selected_provider=None) -> None:
        self.selected_provider = selected_provider
        self.calls = []

    def select(
        self,
        request,
        provider_health,
    ):
        self.calls.append(
            (request, provider_health)
        )
        return self.selected_provider


def _request() -> CapabilityRequest:
    return CapabilityRequest(
        capability_id="lesson.pedagogical_proposal",
        capability_version="1.0",
        input_data={"topic": "fractions"},
    )


def _health() -> ProviderHealth:
    return ProviderHealth(
        status=ProviderStatus.ACTIVE,
        is_available=True,
    )


def test_planner_creates_execution_plan_for_selected_provider():
    registry = ProviderRegistry()
    provider = FakeProvider("provider-a")
    registry.register(provider)

    policy = FakeRoutingPolicy(provider)

    planner = ExecutionPlanner(
        provider_registry=registry,
        routing_policy=policy,
    )

    request = _request()
    health = {
        "provider-a": _health(),
    }

    result = planner.plan(
        request=request,
        provider_health=health,
    )

    assert result == ExecutionPlan(
        capability_id="lesson.pedagogical_proposal",
        capability_version="1.0",
        provider_id="provider-a",
    )


def test_planner_passes_request_and_health_to_routing_policy():
    registry = ProviderRegistry()
    provider = FakeProvider("provider-a")
    registry.register(provider)

    policy = FakeRoutingPolicy(provider)

    planner = ExecutionPlanner(
        provider_registry=registry,
        routing_policy=policy,
    )

    request = _request()
    health = {
        "provider-a": _health(),
    }

    planner.plan(
        request=request,
        provider_health=health,
    )

    assert policy.calls == [
        (request, health),
    ]


def test_planner_returns_none_when_policy_selects_no_provider():
    registry = ProviderRegistry()
    policy = FakeRoutingPolicy(None)

    planner = ExecutionPlanner(
        provider_registry=registry,
        routing_policy=policy,
    )

    result = planner.plan(
        request=_request(),
        provider_health={},
    )

    assert result is None


def test_planner_rejects_provider_not_registered_in_registry():
    registry = ProviderRegistry()

    unregistered_provider = FakeProvider(
        "provider-unregistered"
    )
    policy = FakeRoutingPolicy(
        unregistered_provider
    )

    planner = ExecutionPlanner(
        provider_registry=registry,
        routing_policy=policy,
    )

    with pytest.raises(ValueError):
        planner.plan(
            request=_request(),
            provider_health={},
        )


def test_planner_has_no_execution_or_acceptance_responsibility():
    forbidden = {
        "execute",
        "fallback",
        "accept",
        "reject",
        "validate",
        "register",
    }

    assert forbidden.isdisjoint(
        ExecutionPlanner.__dict__
    )