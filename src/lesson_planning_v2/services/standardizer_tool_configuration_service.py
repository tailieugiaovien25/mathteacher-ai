from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from lesson_planning_v2.services.configuration_hierarchy import merge_with_parent_authority


TOOL_PROFILE_PREFIX = "STANDARDIZER_TOOL::"
COMMON_PROFILE_CODE = TOOL_PROFILE_PREFIX + "GLOBAL"


@dataclass(frozen=True)
class ResolvedStandardizerToolConfiguration:
    common_payload: Mapping[str, Any]
    subject_payload: Mapping[str, Any]
    effective_payload: Mapping[str, Any]
    common_profile: Mapping[str, Any] | None
    subject_profile: Mapping[str, Any] | None


class StandardizerToolConfigurationService:
    def __init__(self, repository) -> None:
        self.repository = repository

    @staticmethod
    def profile_code(subject_ref: str = "") -> str:
        subject = str(subject_ref or "").strip().upper()
        return COMMON_PROFILE_CODE if not subject else TOOL_PROFILE_PREFIX + subject

    def _active(self, code: str):
        profiles = [
            row for row in self.repository.list_profiles()
            if str(row.get("profile_code") or "") == code
            and str(row.get("lifecycle_status") or "") == "ACTIVE"
        ]
        profiles.sort(key=lambda row: str(row.get("profile_id") or ""))
        for profile in profiles:
            version_id = str(profile.get("current_version_id") or "")
            if not version_id:
                continue
            version = self.repository.get_version(configuration_version_id=version_id)
            if not version or version.get("version_status") != "PUBLISHED":
                continue
            payload = version.get("configuration_payload") or {}
            return profile, (payload if isinstance(payload, dict) else {})
        return None, {}

    def resolve(self, *, subject_ref: str = "") -> ResolvedStandardizerToolConfiguration:
        common_profile, common = self._active(COMMON_PROFILE_CODE)
        subject_profile, subject = (None, {})
        if str(subject_ref or "").strip():
            subject_profile, subject = self._active(self.profile_code(subject_ref))
        # Separate namespaces prevent lesson configuration and subject controls
        # from overriding common tool policy.
        effective, _ = merge_with_parent_authority(parent=common, child=subject)
        common_actions = set((common.get("tool_common") or {}).get("allowed_actions") or [])
        controls = dict((effective.get("subject_controls") or {}))
        if common_actions and "allowed_actions" in controls:
            controls["allowed_actions"] = [
                action for action in controls["allowed_actions"] if action in common_actions
            ]
            effective["subject_controls"] = controls
        return ResolvedStandardizerToolConfiguration(
            common_payload=common, subject_payload=subject,
            effective_payload=effective, common_profile=common_profile,
            subject_profile=subject_profile,
        )
