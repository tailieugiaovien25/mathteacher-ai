from __future__ import annotations

from typing import Any

from portal_v2.authorization.portal_authorization import (
    PORTAL_ROLE_TEACHER,
)
from portal_v2.authorization.portal_role_source import (
    PortalRoleResolution,
    TrustedPortalRoleSource,
)


class SupabaseTrustedPortalRoleSource(
    TrustedPortalRoleSource
):
    """
    Supabase-backed trusted role source.

    The adapter reads from a dedicated server-governed role table.
    Absence, malformed data, or read failure falls back safely to
    an untrusted teacher resolution.
    """

    TABLE_NAME = "portal_roles"
    SOURCE_REF = "SUPABASE_PORTAL_ROLES"

    def __init__(
        self,
        *,
        client: Any,
    ) -> None:
        if client is None:
            raise ValueError(
                "client must not be None"
            )

        self._client = client

    def resolve_role(
        self,
        *,
        user_id: str,
    ) -> PortalRoleResolution:
        normalized_user_id = (
            self._normalize_user_id(
                user_id
            )
        )

        try:
            response = (
                self._client
                .table(self.TABLE_NAME)
                .select("user_id,role")
                .eq(
                    "user_id",
                    normalized_user_id,
                )
                .limit(1)
                .execute()
            )
        except Exception:
            return self._fallback(
                normalized_user_id
            )

        data = getattr(
            response,
            "data",
            None,
        )

        if (
            not isinstance(data, list)
            or len(data) != 1
            or not isinstance(data[0], dict)
        ):
            return self._fallback(
                normalized_user_id
            )

        record = data[0]

        returned_user_id = str(
            record.get(
                "user_id",
                "",
            )
            or ""
        ).strip()

        if returned_user_id != normalized_user_id:
            return self._fallback(
                normalized_user_id
            )

        role = str(
            record.get(
                "role",
                "",
            )
            or ""
        ).strip().lower()

        try:
            return PortalRoleResolution(
                user_id=normalized_user_id,
                role=role,
                source_ref=self.SOURCE_REF,
                trusted=True,
            )
        except (
            TypeError,
            ValueError,
        ):
            return self._fallback(
                normalized_user_id
            )

    @classmethod
    def _fallback(
        cls,
        user_id: str,
    ) -> PortalRoleResolution:
        return PortalRoleResolution(
            user_id=user_id,
            role=PORTAL_ROLE_TEACHER,
            source_ref=cls.SOURCE_REF,
            trusted=False,
        )

    @staticmethod
    def _normalize_user_id(
        user_id: str,
    ) -> str:
        if not isinstance(
            user_id,
            str,
        ):
            raise TypeError(
                "user_id must be str"
            )

        normalized = user_id.strip()

        if not normalized:
            raise ValueError(
                "user_id must not be empty"
            )

        return normalized
