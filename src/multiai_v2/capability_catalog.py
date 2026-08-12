from __future__ import annotations

from src.multiai_v2.contracts import ProviderCapability


class CapabilityCatalog:
    """
    Canonical catalog of capabilities known to the Multi-AI subsystem.

    The catalog owns capability registration and lookup only.

    It MUST NOT:
    - select or rank providers;
    - perform routing;
    - execute providers;
    - perform fallback;
    - validate domain output;
    - make business acceptance decisions.
    """

    def __init__(self) -> None:
        self._capabilities: dict[
            tuple[str, str],
            ProviderCapability,
        ] = {}

    def register(
        self,
        capability: ProviderCapability,
    ) -> None:
        if not isinstance(
            capability,
            ProviderCapability,
        ):
            raise TypeError(
                "capability must be ProviderCapability"
            )

        key = (
            capability.capability_id,
            capability.version,
        )

        if key in self._capabilities:
            raise ValueError(
                "capability is already registered"
            )

        self._capabilities[key] = capability

    def get(
        self,
        capability_id: str,
        version: str,
    ) -> ProviderCapability | None:
        capability_id = capability_id.strip()
        version = version.strip()

        if not capability_id:
            raise ValueError(
                "capability_id must not be empty"
            )

        if not version:
            raise ValueError(
                "version must not be empty"
            )

        return self._capabilities.get(
            (
                capability_id,
                version,
            )
        )

    def capabilities(
        self,
    ) -> tuple[ProviderCapability, ...]:
        return tuple(
            self._capabilities.values()
        )