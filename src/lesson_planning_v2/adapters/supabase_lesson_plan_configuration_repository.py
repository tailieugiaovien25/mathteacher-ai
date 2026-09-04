from __future__ import annotations

from typing import Any

from lesson_planning_v2.models.lesson_plan_configuration import (
    LessonPlanConfigurationSnapshot,
)


class SupabaseLessonPlanConfigurationRepository:
    PROFILE_TABLE = "lesson_plan_configuration_profiles"
    VERSION_TABLE = "lesson_plan_configuration_versions"
    TOOL_PROFILE_PREFIXES = ("TOOL::", "STANDARDIZER_TOOL::")

    def __init__(self, client) -> None:
        self.client = client

    @staticmethod
    def _rows(response) -> list[dict[str, Any]]:
        data = getattr(response, "data", None)
        if not data:
            return []
        return [dict(item) for item in data]

    def _equivalent_subject_refs(self, subject_ref: str) -> set[str]:
        subject = str(subject_ref or "").strip()
        refs = {subject} if subject else set()
        if not subject:
            return refs
        try:
            from educational_planning_v2.adapters.supabase_subject_catalog_repository import (
                SupabaseSubjectCatalogRepository,
            )
            catalog = SupabaseSubjectCatalogRepository(client=self.client)
            for item in tuple(catalog.list_subjects() or ()):
                item_id = str(getattr(item, "subject_id", "") or "").strip()
                item_code = str(getattr(item, "code", "") or "").strip()
                if subject.casefold() in {item_id.casefold(), item_code.casefold()}:
                    if item_id:
                        refs.add(item_id)
                    if item_code:
                        refs.add(item_code)
                    break
        except Exception:
            # Compatibility lookup must never remove the existing exact/global fallback.
            return refs
        return refs

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
        return [
            row for row in self._rows(response)
            if not str(row.get("profile_code") or "").startswith(
                self.TOOL_PROFILE_PREFIXES
            )
        ]

    def get_active_configuration_exact(
        self, *, subject_ref: str, component_ref: str | None = None
    ) -> LessonPlanConfigurationSnapshot | None:
        subject = str(subject_ref or "").strip()
        component = str(component_ref or "").strip()
        matches = []
        equivalent_subjects = self._equivalent_subject_refs(subject)
        for row in self._active_profiles():
            row_subject = str(row.get("subject_ref") or "").strip()
            row_component = str(row.get("component_ref") or "").strip()
            if row_subject in equivalent_subjects and row_component == component:
                matches.append(row)
            elif not subject and not row_subject and not row_component:
                matches.append(row)
        matches.sort(key=lambda row: str(row.get("profile_code") or ""))
        for profile in matches:
            current_version_id = str(profile.get("current_version_id") or "").strip()
            if not current_version_id:
                continue
            version = self._published_version(configuration_version_id=current_version_id)
            if version is None or str(version.get("profile_id") or "") != str(profile.get("profile_id") or ""):
                continue
            payload = version.get("configuration_payload") or {}
            return LessonPlanConfigurationSnapshot(
                profile_id=str(profile.get("profile_id") or ""),
                profile_code=str(profile.get("profile_code") or ""),
                profile_name=str(profile.get("profile_name") or ""),
                subject_ref=str(profile.get("subject_ref") or ""),
                component_ref=str(profile.get("component_ref") or ""),
                configuration_version_id=str(version.get("configuration_version_id") or ""),
                version_number=int(version.get("version_number") or 0),
                configuration_payload=payload if isinstance(payload, dict) else {},
            )
        return None

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

        profiles = self._active_profiles()
        candidates: list[tuple[int, dict[str, Any]]] = []
        for row in profiles:
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

        if not any(rank < 2 for rank, _ in candidates):
            equivalent_subjects = self._equivalent_subject_refs(subject)
            equivalent_subjects.discard(subject)
            for row in profiles:
                row_subject = str(row.get("subject_ref") or "").strip()
                row_component = str(row.get("component_ref") or "").strip()
                if row_subject not in equivalent_subjects:
                    continue
                if row_component == component:
                    rank = 0
                elif not row_component:
                    rank = 1
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
