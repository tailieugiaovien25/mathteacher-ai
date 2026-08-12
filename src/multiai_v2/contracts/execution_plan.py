from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionPlan:
    """
    Canonical provider-neutral plan for one AI capability execution.

    ExecutionPlan records the capability identity and the provider
    assigned to execute it.

    It MUST NOT:
    - execute capabilities;
    - perform fallback;
    - validate domain correctness;
    - make business acceptance decisions;
    - select or rank providers.
    """

    capability_id: str
    capability_version: str
    provider_id: str

    def __post_init__(self) -> None:
        capability_id = self.capability_id.strip()
        capability_version = self.capability_version.strip()
        provider_id = self.provider_id.strip()

        if not capability_id:
            raise ValueError(
                "capability_id must not be empty"
            )

        if not capability_version:
            raise ValueError(
                "capability_version must not be empty"
            )

        if not provider_id:
            raise ValueError(
                "provider_id must not be empty"
            )

        object.__setattr__(
            self,
            "capability_id",
            capability_id,
        )
        object.__setattr__(
            self,
            "capability_version",
            capability_version,
        )
        object.__setattr__(
            self,
            "provider_id",
            provider_id,
        )