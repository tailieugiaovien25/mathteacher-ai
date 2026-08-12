from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutionResult:
    """
    Canonical provider-neutral result of one AI capability execution.

    ExecutionResult records what happened during provider execution.

    It MUST NOT:
    - validate domain correctness;
    - accept or reject business output;
    - select providers;
    - perform routing;
    - perform fallback.
    """

    capability_id: str
    capability_version: str
    provider_id: str
    output_data: Any
    success: bool
    error: str | None = None

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

        if not isinstance(self.success, bool):
            raise TypeError(
                "success must be bool"
            )

        if self.error is not None:
            error = self.error.strip()
            if not error:
                raise ValueError(
                    "error must not be empty when provided"
                )
            object.__setattr__(
                self,
                "error",
                error,
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