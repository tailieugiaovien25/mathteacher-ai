from __future__ import annotations

from dataclasses import dataclass

from src.multiai_v2.contracts.collaboration_role import (
    CollaborationRole,
)


@dataclass(frozen=True)
class CollaborationPlan:
    """
    Provider-neutral plan for one Multi-AI collaboration.

    CollaborationPlan defines the roles required by a collaboration
    without binding those roles to specific providers.

    It MUST NOT:
    - bind roles to providers;
    - select or route providers;
    - execute capabilities;
    - perform fallback;
    - validate domain correctness;
    - make business acceptance decisions.
    """

    collaboration_id: str
    roles: tuple[CollaborationRole, ...]

    def __post_init__(self) -> None:
        collaboration_id = self.collaboration_id.strip()

        if not collaboration_id:
            raise ValueError(
                "collaboration_id must not be empty"
            )

        if not isinstance(self.roles, tuple):
            raise TypeError(
                "roles must be tuple"
            )

        if not self.roles:
            raise ValueError(
                "roles must not be empty"
            )

        if not all(
            isinstance(role, CollaborationRole)
            for role in self.roles
        ):
            raise TypeError(
                "every role must be CollaborationRole"
            )

        role_ids = tuple(
            role.role_id
            for role in self.roles
        )

        if len(role_ids) != len(set(role_ids)):
            raise ValueError(
                "role_id must be unique within collaboration"
            )

        object.__setattr__(
            self,
            "collaboration_id",
            collaboration_id,
        )