from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from portal_v2.authorization.portal_role_source import (
    TrustedPortalRoleSource,
)
from portal_v2.authorization.supabase_portal_role_source import (
    SupabaseTrustedPortalRoleSource,
)


class PortalSessionValidationError(PermissionError):
    """Raised when a cached portal session can no longer be trusted."""


@dataclass(frozen=True)
class ValidatedPortalSession:
    """Server-validated Supabase identity plus fresh trusted portal role."""

    user_id: str
    email: str
    role: str


def validate_supabase_portal_session(
    *,
    client: Any,
    expected_user_id: str,
    role_source: TrustedPortalRoleSource | None = None,
) -> ValidatedPortalSession:
    """Validate current Auth identity and re-resolve trusted authorization.

    ``auth.get_user()`` asks Supabase Auth for the current authenticated user,
    so cached Streamlit session markers are never treated as proof that the
    Auth session is still valid. Authorization is then read again from the
    server-governed portal role source. User metadata is never used to grant
    teacher or administrator access.
    """

    if client is None:
        raise PortalSessionValidationError(
            "Supabase client is not available."
        )

    normalized_expected_user_id = _required_text(
        expected_user_id,
        "expected_user_id",
    )

    try:
        response = client.auth.get_user()
    except Exception as error:
        raise PortalSessionValidationError(
            "Supabase Auth could not validate the current session."
        ) from error

    user = getattr(response, "user", None)
    actual_user_id = str(
        getattr(user, "id", "") or ""
    ).strip()
    if not actual_user_id:
        raise PortalSessionValidationError(
            "Supabase Auth returned no authenticated user."
        )
    if actual_user_id != normalized_expected_user_id:
        raise PortalSessionValidationError(
            "Authenticated user does not match the cached portal identity."
        )

    email = str(
        getattr(user, "email", "") or ""
    ).strip()
    if not email:
        raise PortalSessionValidationError(
            "Authenticated portal user has no email identity."
        )

    source = role_source or SupabaseTrustedPortalRoleSource(
        client=client
    )
    try:
        resolution = source.resolve_role(
            user_id=actual_user_id
        )
    except Exception as error:
        raise PortalSessionValidationError(
            "Portal authorization could not be revalidated."
        ) from error

    if not resolution.can_access_portal:
        raise PortalSessionValidationError(
            "Portal account is not active or not trusted."
        )

    return ValidatedPortalSession(
        user_id=actual_user_id,
        email=email,
        role=resolution.effective_role,
    )


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise PortalSessionValidationError(
            f"{field_name} must be str."
        )
    normalized = value.strip()
    if not normalized:
        raise PortalSessionValidationError(
            f"{field_name} must not be empty."
        )
    return normalized
