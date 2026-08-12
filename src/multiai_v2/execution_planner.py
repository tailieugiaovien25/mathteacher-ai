from __future__ import annotations

from src.multiai_v2.contracts import (
    CapabilityRequest,
    ExecutionPlan,
    ProviderHealth,
)
from src.multiai_v2.provider_registry import ProviderRegistry
from src.multiai_v2.routing_policy import RoutingPolicy


class ExecutionPlanner:
    """
    Creates a provider-neutral execution plan for one capability request.

    ExecutionPlanner coordinates provider selection through RoutingPolicy
    and verifies that the selected provider belongs to ProviderRegistry.

    It MUST NOT:
    - execute capabilities;
    - perform fallback;
    - validate domain correctness;
    - make business acceptance decisions;
    - register providers.
    """

    def __init__(
        self,
        provider_registry: ProviderRegistry,
        routing_policy: RoutingPolicy,
    ) -> None:
        self._provider_registry = provider_registry
        self._routing_policy = routing_policy

    def plan(
        self,
        request: CapabilityRequest,
        provider_health: dict[str, ProviderHealth],
    ) -> ExecutionPlan | None:
        provider = self._routing_policy.select(
            request=request,
            provider_health=provider_health,
        )

        if provider is None:
            return None

        registered_provider = self._provider_registry.get(
            provider.provider_id
        )

        if registered_provider is not provider:
            raise ValueError(
                "routing policy selected a provider "
                "not registered in ProviderRegistry"
            )

        return ExecutionPlan(
            capability_id=request.capability_id,
            capability_version=request.capability_version,
            provider_id=provider.provider_id,
        )