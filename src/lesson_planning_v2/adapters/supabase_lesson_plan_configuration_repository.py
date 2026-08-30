from __future__ import annotations

from typing import Any

from lesson_planning_v2.models.lesson_plan_configuration import (
    LessonPlanConfigurationSnapshot,
)


class SupabaseLessonPlanConfigurationRepository:
    PROFILE_TABLE = "lesson_plan_configuration_profiles"
    VERSION_TABLE = "lesson_plan_configuration_versions"

    def __init__(self, client) -> None:
        self.client = client

    @staticmethod
    def _rows(response) -> list[dict[str, Any]]:
        data = getattr(response, "data", None)
        if not data:
            return []
        return [dict(item) for item in data]

    def _active_profiles(self) -> list[dict[str, Any]]:
        response = (
            self.client.table(self.PROFILE_TABLE)
            .select(
                "profile_id,profile_code,profile_name,"
                "subject_ref,component_ref,current_version_id,lifecycle_status"
            )
            .eq("lifecycle_status", "ACTIVE")
            .execute()
        )
        return self._rows(response)

    def _published_version(
        self,
        *,
        configuration_version_id: str,
    ) -> dict[str, Any] | None:
        response = (
            self.client.table(self.VERSION_TABLE)
            .select(
                "configuration_version_id,profile_id,"
                "version_number,version_status,configuration_payload"
            )
            .eq("configuration_version_id", configuration_version_id)
            .eq("version_status", "PUBLISHED")
            .execute()
        )
        rows = self._rows(response)
        return rows[0] if rows else None

    def get_active_configuration(
        self,
        *,
        subject_ref: str,
        component_ref: str | None = None,
    ) -> LessonPlanConfigurationSnapshot | None:
        subject = str(subject_ref or "").strip()
        component = str(component_ref or "").strip()

        candidates: list[tuple[int, dict[str, Any]]] = []
        for row in self._active_profiles():
            row_subject = str(row.get("subject_ref") or "").strip()
            row_component = str(row.get("component_ref") or "").strip()

            if row_subject == subject and row_component == component:
                rank = 0
            elif row_subject == subject and not row_component:
                rank = 1
            elif not row_subject and not row_component:
                rank = 2
            else:
                continue
            candidates.append((rank, row))

        candidates.sort(
            key=lambda item: (
                item[0],
                str(item[1].get("profile_code") or ""),
            )
        )

        for _, profile in candidates:
            current_version_id = str(
                profile.get("current_version_id") or ""
            ).strip()
            if not current_version_id:
                continue
            version = self._published_version(
                configuration_version_id=current_version_id,
            )
            if version is None:
                continue
            if str(version.get("profile_id") or "") != str(
                profile.get("profile_id") or ""
            ):
                continue

            payload = version.get("configuration_payload") or {}
            if not isinstance(payload, dict):
                payload = {}

            return LessonPlanConfigurationSnapshot(
                profile_id=str(profile.get("profile_id") or ""),
                profile_code=str(profile.get("profile_code") or ""),
                profile_name=str(profile.get("profile_name") or ""),
                subject_ref=str(profile.get("subject_ref") or ""),
                component_ref=str(profile.get("component_ref") or ""),
                configuration_version_id=str(
                    version.get("configuration_version_id") or ""
                ),
                version_number=int(version.get("version_number") or 0),
                configuration_payload=payload,
            )
        return None
