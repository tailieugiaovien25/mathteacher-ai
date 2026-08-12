from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.multiai_v2.contracts import (
    CapabilityRequest,
    ExecutionResult,
    ProviderCapability,
)


@runtime_checkable
class AIProvider(Protocol):
    """
    Provider-neutral execution interface for Multi-AI providers.

    Implementations expose identity, declared capabilities, and
    capability execution.

    AIProvider MUST NOT:
    - select or rank providers;
    - perform routing;
    - perform fallback;
    - perform domain validation;
    - make business acceptance decisions.
    """

    @property
    def provider_id(self) -> str:
        ...

    def capabilities(
        self,
    ) -> tuple[ProviderCapability, ...]:
        ...

    def execute(
        self,
        request: CapabilityRequest,
    ) -> ExecutionResult:
        ...