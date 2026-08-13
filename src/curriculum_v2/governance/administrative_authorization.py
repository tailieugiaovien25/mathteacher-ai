from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from curriculum_v2.governance.data_trust_governance import (
    AdministrativeVerification,
)


class GovernancePermission(str, Enum):
    ENTER_DATA = "ENTER_DATA"
    VERIFY_DATA = "VERIFY_DATA"
    PUBLISH_DATA = "PUBLISH_DATA"
    SUPERSEDE_DATA = "SUPERSEDE_DATA"


@dataclass(frozen=True)
class GovernanceActor:
    """
    Identity + granted governance permissions.

    Roles and permissions are independent from educational
    subjects, grades, curricula, textbooks, and data values.
    """

    actor_id: str
    permissions: tuple[GovernancePermission, ...]

    def __post_init__(self) -> None:
        if not isinstance(
            self.actor_id,
            str,
        ):
            raise TypeError(
                "actor_id must be str"
            )

        actor_id = self.actor_id.strip()

        if not actor_id:
            raise ValueError(
                "actor_id must not be empty"
            )

        object.__setattr__(
            self,
            "actor_id",
            actor_id,
        )

        if not isinstance(
            self.permissions,
            tuple,
        ):
            raise TypeError(
                "permissions must be tuple"
            )

        normalized = []

        for permission in self.permissions:
            if not isinstance(
                permission,
                GovernancePermission,
            ):
                raise TypeError(
                    "permissions must contain "
                    "GovernancePermission values"
                )

            if permission not in normalized:
                normalized.append(
                    permission
                )

        object.__setattr__(
            self,
            "permissions",
            tuple(normalized),
        )

    def has_permission(
        self,
        permission: GovernancePermission,
    ) -> bool:
        if not isinstance(
            permission,
            GovernancePermission,
        ):
            raise TypeError(
                "permission must be GovernancePermission"
            )

        return permission in self.permissions


class GovernanceAuthorizationPolicy:
    """
    Stable authorization policy for administrative data governance.

    It decides whether an actor may perform a governance action.
    It owns no educational data and no physical user store.
    """

    @staticmethod
    def is_allowed(
        *,
        actor: GovernanceActor,
        permission: GovernancePermission,
    ) -> bool:
        if not isinstance(
            actor,
            GovernanceActor,
        ):
            raise TypeError(
                "actor must be GovernanceActor"
            )

        if not isinstance(
            permission,
            GovernancePermission,
        ):
            raise TypeError(
                "permission must be GovernancePermission"
            )

        return actor.has_permission(
            permission
        )

    @classmethod
    def require(
        cls,
        *,
        actor: GovernanceActor,
        permission: GovernancePermission,
    ) -> None:
        if not cls.is_allowed(
            actor=actor,
            permission=permission,
        ):
            raise PermissionError(
                f"actor {actor.actor_id!r} "
                f"does not have permission "
                f"{permission.value!r}"
            )


class AdministrativeVerificationPolicy:
    """
    Creates an AdministrativeVerification only after
    authorization has succeeded.

    The verifier identity comes from the authorized actor,
    not from an arbitrary caller-provided string.
    """

    @staticmethod
    def create_verification(
        *,
        entered_by: str,
        verifier: GovernanceActor,
        verified_at: datetime,
        source_reference: str | None = None,
    ) -> AdministrativeVerification:
        GovernanceAuthorizationPolicy.require(
            actor=verifier,
            permission=GovernancePermission.VERIFY_DATA,
        )

        if not isinstance(
            entered_by,
            str,
        ):
            raise TypeError(
                "entered_by must be str"
            )

        entered_by = entered_by.strip()

        if not entered_by:
            raise ValueError(
                "entered_by must not be empty"
            )

        return AdministrativeVerification(
            entered_by=entered_by,
            verified_by=verifier.actor_id,
            verified_at=verified_at,
            source_reference=source_reference,
        )
