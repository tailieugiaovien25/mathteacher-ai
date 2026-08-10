from __future__ import annotations

from typing import Any


class RecognitionProviderResolver:
    """
    V2 Recognition Provider Resolver.

    Responsibility:
    - Select a recognition provider through the provider registry.
    - Keep provider lookup logic outside orchestration/dispatch layers.

    This component MUST NOT:
    - execute processors;
    - modify dispatch state;
    - mutate input;
    - bypass the provider registry.
    """

    def __init__(self, provider_registry: Any) -> None:
        if provider_registry is None:
            raise ValueError("provider_registry is required")

        self._provider_registry = provider_registry

    def resolve(self, provider_name: str) -> Any:
        """
        Resolve a recognition provider by its registered name.
        """

        if not isinstance(provider_name, str):
            raise TypeError("provider_name must be a string")

        normalized_name = provider_name.strip()

        if not normalized_name:
            raise ValueError("provider_name must not be empty")

        return self._provider_registry.get(normalized_name)