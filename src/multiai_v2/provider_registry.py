from __future__ import annotations

from src.multiai_v2.provider import AIProvider


class ProviderRegistry:
    """
    Registry of AI providers available to the Multi-AI subsystem.

    ProviderRegistry owns provider registration and lookup only.

    It MUST NOT:
    - select or rank providers;
    - perform routing;
    - perform fallback;
    - execute capabilities;
    - make business acceptance decisions.
    """

    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register(
        self,
        provider: AIProvider,
    ) -> None:
        if not isinstance(provider, AIProvider):
            raise TypeError(
                "provider must satisfy AIProvider"
            )

        provider_id = provider.provider_id.strip()

        if not provider_id:
            raise ValueError(
                "provider_id must not be empty"
            )

        if provider_id in self._providers:
            raise ValueError(
                f"provider already registered: {provider_id}"
            )

        self._providers[provider_id] = provider

    def get(
        self,
        provider_id: str,
    ) -> AIProvider | None:
        provider_id = provider_id.strip()

        if not provider_id:
            raise ValueError(
                "provider_id must not be empty"
            )

        return self._providers.get(provider_id)

    def providers(
        self,
    ) -> tuple[AIProvider, ...]:
        return tuple(self._providers.values())