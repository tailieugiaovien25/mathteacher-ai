"""ADMIN-only write repository for lesson-plan configuration governance."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


class LessonPlanConfigurationAdminWriteError(RuntimeError):
    pass


class SupabaseLessonPlanConfigurationAdminRepository:
    PROFILE_TABLE = "lesson_plan_configuration_profiles"
    VERSION_TABLE = "lesson_plan_configuration_versions"

    def __init__(self, client: Any) -> None:
        self._client = client

    def _current_user_id(self) -> str:
        auth = getattr(self._client, "auth", None)
        if auth is None or not hasattr(auth, "get_user"):
            raise LessonPlanConfigurationAdminWriteError(
                "Authenticated ADMIN user is required to publish."
            )
        response = auth.get_user()
        user = getattr(response, "user", None)
        user_id = getattr(user, "id", None)
        if not user_id:
            raise LessonPlanConfigurationAdminWriteError(
                "Authenticated ADMIN user id is unavailable."
            )
        return str(user_id)


    @staticmethod
    def _rows(response: Any) -> list[dict[str, Any]]:
        data = getattr(response, "data", None)
        if not data:
            return []
        return [dict(row) for row in data]

    @staticmethod
    def _one(response: Any, *, operation: str) -> dict[str, Any]:
        rows = SupabaseLessonPlanConfigurationAdminRepository._rows(response)
        if not rows:
            raise LessonPlanConfigurationAdminWriteError(
                f"{operation} returned no row"
            )
        return rows[0]

    def get_profile(self, *, profile_id: str) -> dict[str, Any] | None:
        response = (
            self._client.table(self.PROFILE_TABLE)
            .select("*")
            .eq("profile_id", profile_id)
            .limit(1)
            .execute()
        )
        rows = self._rows(response)
        return rows[0] if rows else None

    def get_version(self, *, configuration_version_id: str) -> dict[str, Any] | None:
        response = (
            self._client.table(self.VERSION_TABLE)
            .select("*")
            .eq("configuration_version_id", configuration_version_id)
            .limit(1)
            .execute()
        )
        rows = self._rows(response)
        return rows[0] if rows else None

    def list_versions(self, *, profile_id: str) -> list[dict[str, Any]]:
        response = (
            self._client.table(self.VERSION_TABLE)
            .select("*")
            .eq("profile_id", profile_id)
            .order("version_number")
            .execute()
        )
        return self._rows(response)

    def create_profile(
        self,
        *,
        profile_code: str,
        profile_name: str,
        subject_ref: str = "",
        component_ref: str = "",
    ) -> dict[str, Any]:
        payload = {
            "profile_code": profile_code.strip(),
            "profile_name": profile_name.strip(),
            "subject_ref": subject_ref.strip(),
            "component_ref": component_ref.strip(),
            "lifecycle_status": "DRAFT",
        }
        response = self._client.table(self.PROFILE_TABLE).insert(payload).execute()
        return self._one(response, operation="create_profile")

    def create_draft_version(
        self,
        *,
        profile_id: str,
        version_number: int,
        configuration_payload: Mapping[str, Any],
        change_note: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "profile_id": profile_id,
            "version_number": int(version_number),
            "version_status": "DRAFT",
            "configuration_payload": dict(configuration_payload),
        }
        if change_note is not None:
            payload["change_note"] = change_note
        response = self._client.table(self.VERSION_TABLE).insert(payload).execute()
        return self._one(response, operation="create_draft_version")

    def update_draft_version(
        self,
        *,
        configuration_version_id: str,
        configuration_payload: Mapping[str, Any],
        change_note: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "configuration_payload": dict(configuration_payload),
        }
        if change_note is not None:
            payload["change_note"] = change_note
        response = (
            self._client.table(self.VERSION_TABLE)
            .update(payload)
            .eq("configuration_version_id", configuration_version_id)
            .eq("version_status", "DRAFT")
            .execute()
        )
        return self._one(response, operation="update_draft_version")

    def publish_version(self, *, configuration_version_id: str) -> dict[str, Any]:
        payload = {
            "version_status": "PUBLISHED",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "published_by": self._current_user_id(),
        }
        response = (
            self._client.table(self.VERSION_TABLE)
            .update(payload)
            .eq("configuration_version_id", configuration_version_id)
            .eq("version_status", "DRAFT")
            .execute()
        )
        return self._one(response, operation="publish_version")

    def set_current_version(
        self,
        *,
        profile_id: str,
        configuration_version_id: str,
        activate_profile: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"current_version_id": configuration_version_id}
        if activate_profile:
            payload["lifecycle_status"] = "ACTIVE"
        response = (
            self._client.table(self.PROFILE_TABLE)
            .update(payload)
            .eq("profile_id", profile_id)
            .execute()
        )
        return self._one(response, operation="set_current_version")

    def delete_profile(self, *, profile_id: str) -> None:
        self._client.table(self.PROFILE_TABLE).delete().eq(
            "profile_id",
            profile_id,
        ).execute()

    def retire_version(self, *, configuration_version_id: str) -> dict[str, Any]:
        response = (
            self._client.table(self.VERSION_TABLE)
            .update({"version_status": "RETIRED"})
            .eq("configuration_version_id", configuration_version_id)
            .eq("version_status", "PUBLISHED")
            .execute()
        )
        return self._one(response, operation="retire_version")
