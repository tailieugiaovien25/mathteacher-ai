from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CollaborationRole:
    """
    Provider-neutral role in a Multi-AI collaboration.

    CollaborationRole describes one collaboration role through the
    capability required to fulfill that role.

    It MUST NOT:
    - bind the role to a specific provider;
    - select or route providers;
    - execute capabilities;
    - perform fallback;
    - validate domain correctness;
    - make business acceptance decisions.
    """

    role_id: str
    capability_id: str
    capability_version: str

    def __post_init__(self) -> None:
        role_id = self.role_id.strip()
        capability_id = self.capability_id.strip()
        capability_version = self.capability_version.strip()

        if not role_id:
            raise ValueError(
                "role_id must not be empty"
            )

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
            "role_id",
            role_id,
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