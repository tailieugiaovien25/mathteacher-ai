from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.multiai_v2.contracts import (
    CapabilityRequest,
    ProviderHealth,
)
from src.multiai_v2.provider import AIProvider


@runtime_checkable
class RoutingPolicy(Protocol):
    """
    Provider-neutral routing policy contract for Multi-AI.

    RoutingPolicy defines how a routing policy selects an eligible
    provider for a capability request using provider runtime health.

    It MUST NOT:
    - execute capabilities;
    - perform fallback;
    - validate domain correctness;
    - make business acceptance decisions;
    - register providers.
    """

    def select(
        self,
        request: CapabilityRequest,
        provider_health: dict[str, ProviderHealth],
    ) -> AIProvider | None:
        ...