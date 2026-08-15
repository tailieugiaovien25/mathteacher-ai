from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from portal_v2.authorization.portal_authorization import (
    PORTAL_ROLE_ADMIN,
    PORTAL_ROLE_TEACHER,
    SUPPORTED_PORTAL_ROLES,
)


@dataclass(frozen=True)
class PortalRoleResolution:
    """
    Canonical result returned by a trusted portal role source.

    This object contains authorization metadata only.
    It contains no educational-domain data and no physical
    storage information.
    """

    user_id: str
    role: str
    source_ref: str
    trusted: bool

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
            "source_ref",
            self._normalize_required_text(
                self.source_ref,
                "source_ref",
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

        if not isinstance(self.trusted, bool):
            raise TypeError(
                "trusted must be bool"
            )

    @property
    def grants_admin_access(self) -> bool:
        return (
            self.trusted
            and
            self.role == PORTAL_ROLE_ADMIN
        )

    @property
    def effective_role(self) -> str:
        """
        Fail-safe role exposed to the portal.

        An untrusted role resolution can never grant ADMIN.
        """
        if self.grants_admin_access:
            return PORTAL_ROLE_ADMIN

        return PORTAL_ROLE_TEACHER

    @staticmethod
    def _normalize_required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be str"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized


class TrustedPortalRoleSource(ABC):
    """
    Stable contract for resolving a user's trusted portal role.

    Implementations may use Supabase or another identity system,
    but callers do not know or depend on the physical source.
    """

    @abstractmethod
    def resolve_role(
        self,
        *,
        user_id: str,
    ) -> PortalRoleResolution:
        raise NotImplementedError
