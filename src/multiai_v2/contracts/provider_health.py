from __future__ import annotations

from dataclasses import dataclass

from src.multiai_v2.contracts.provider_status import (
    ProviderStatus,
)


@dataclass(frozen=True)
class ProviderHealth:
    """
    Runtime health snapshot of an AI provider.

    ProviderHealth describes runtime condition only.
    It does not describe provider capability.

    Responsibilities:
    - expose current provider status;
    - expose availability;
    - expose latency and failure signals;
    - remain immutable.

    ProviderHealth MUST NOT:
    - select providers;
    - perform routing;
    - contain business logic;
    - modify provider lifecycle.
    """

    status: ProviderStatus
    is_available: bool

    latency_ms: float | None = None
    failure_rate: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            ProviderStatus,
        ):
            raise TypeError(
                "status must be ProviderStatus"
            )

        if not isinstance(
            self.is_available,
            bool,
        ):
            raise TypeError(
                "is_available must be bool"
            )

        if (
            self.latency_ms is not None
            and self.latency_ms < 0.0
        ):
            raise ValueError(
                "latency_ms must be >= 0"
            )

        if not (
            0.0
            <= self.failure_rate
            <= 1.0
        ):
            raise ValueError(
                "failure_rate must be within [0, 1]"
            )