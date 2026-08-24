from __future__ import annotations

from dataclasses import dataclass

from curriculum_v2.governance.administrative_authorization import (
    GovernanceActor,
    GovernancePermission,
)


PORTAL_ROLE_TEACHER = "teacher"
PORTAL_ROLE_ADMIN = "admin"

SUPPORTED_PORTAL_ROLES = (
    PORTAL_ROLE_TEACHER,
    PORTAL_ROLE_ADMIN,
)


@dataclass(frozen=True)
class PortalAuthorizationContext:
    """
    Authentication-independent authorization context.

    Identity may come from Supabase, another identity provider,
    or test/runtime configuration. This contract owns no
    authentication or storage logic.
    """

    user_id: str
    email: str
    role: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "user_id",
            self._normalize_required_text(
                self.user_id,
                "user_id",
            ),
        )

        object.__setattr__(
            self,
            "email",
            self._normalize_required_text(
                self.email,
                "email",
            ),
        )

        normalized_role = (
            self._normalize_required_text(
                self.role,
                "role",
            )
            .lower()
        )

        if normalized_role not in SUPPORTED_PORTAL_ROLES:
            raise ValueError(
                f"unsupported portal role: {normalized_role}"
            )

        object.__setattr__(
            self,
            "role",
            normalized_role,
        )

    @property
    def is_admin(self) -> bool:
        return self.role == PORTAL_ROLE_ADMIN

    @property
    def can_access_admin_portal(self) -> bool:
        return self.is_admin

    def to_governance_actor(self) -> GovernanceActor:
        if self.role == PORTAL_ROLE_ADMIN:
            permissions = (
                GovernancePermission.ENTER_DATA,
                GovernancePermission.VERIFY_DATA,
                GovernancePermission.PUBLISH_DATA,
                GovernancePermission.SUPERSEDE_DATA,
            )
        else:
            permissions = ()

        return GovernanceActor(
            actor_id=self.user_id,
            permissions=permissions,
        )

    @staticmethod
    def _normalize_required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be str"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized


def build_portal_authorization_context(
    *,
    user_id: str,
    email: str,
    role: str,
) -> PortalAuthorizationContext:
    """
    Boundary factory.

    Role must be supplied by an authentication/profile/metadata
    source. This function never infers authorization from email.
    """

    return PortalAuthorizationContext(
        user_id=user_id,
        email=email,
        role=role,
    )
