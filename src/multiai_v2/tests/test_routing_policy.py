from typing import Protocol, runtime_checkable

from src.multiai_v2.contracts import (
    CapabilityRequest,
    ProviderHealth,
)
from src.multiai_v2.provider import AIProvider
from src.multiai_v2.routing_policy import RoutingPolicy


def test_routing_policy_is_protocol():
    assert getattr(
        RoutingPolicy,
        "_is_protocol",
        False,
    ) is True


def test_routing_policy_is_runtime_checkable():
    assert getattr(
        RoutingPolicy,
        "_is_runtime_protocol",
        False,
    ) is True


def test_structural_policy_satisfies_protocol():
    class FakeRoutingPolicy:
        def select(
            self,
            request: CapabilityRequest,
            providers: tuple[AIProvider, ...],
            provider_health: dict[str, ProviderHealth],
        ) -> AIProvider | None:
            return None

    policy = FakeRoutingPolicy()

    assert isinstance(policy, RoutingPolicy)


def test_policy_exposes_select_contract():
    assert "select" in RoutingPolicy.__dict__


def test_policy_has_no_execution_responsibility():
    forbidden = {
        "execute",
        "fallback",
        "accept",
        "reject",
        "validate",
        "register",
    }

    assert forbidden.isdisjoint(
        RoutingPolicy.__dict__
    )