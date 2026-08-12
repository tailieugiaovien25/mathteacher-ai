from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CapabilityRequest:
    """
    Canonical provider-neutral request for one AI capability.

    CapabilityRequest describes what capability is required and the
    trusted input supplied for execution.

    It MUST NOT:
    - select a provider;
    - contain provider-specific configuration;
    - perform routing;
    - contain business acceptance logic.
    """

    capability_id: str
    capability_version: str
    input_data: Any
    context: Any | None = None

    def __post_init__(self) -> None:
        capability_id = self.capability_id.strip()
        capability_version = self.capability_version.strip()

        if not capability_id:
            raise ValueError(
                "capability_id must not be empty"
            )

        if not capability_version:
            raise ValueError(
                "capability_version must not be empty"
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
