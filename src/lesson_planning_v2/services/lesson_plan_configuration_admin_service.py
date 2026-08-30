"""ADMIN orchestration for lesson-plan configuration version governance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


class LessonPlanConfigurationAdminError(RuntimeError):
    pass


class LessonPlanConfigurationAdminRepositoryProtocol(Protocol):
    def get_profile(self, *, profile_id: str) -> dict[str, Any] | None: ...
    def get_version(self, *, configuration_version_id: str) -> dict[str, Any] | None: ...
    def list_versions(self, *, profile_id: str) -> list[dict[str, Any]]: ...
    def create_profile(self, **kwargs: Any) -> dict[str, Any]: ...
    def create_draft_version(self, **kwargs: Any) -> dict[str, Any]: ...
    def update_draft_version(self, **kwargs: Any) -> dict[str, Any]: ...
    def publish_version(self, **kwargs: Any) -> dict[str, Any]: ...
    def set_current_version(self, **kwargs: Any) -> dict[str, Any]: ...
    def retire_version(self, **kwargs: Any) -> dict[str, Any]: ...


@dataclass(frozen=True)
class LessonPlanConfigurationActivationResult:
    profile: dict[str, Any]
    current_version: dict[str, Any]
    retired_previous_version: dict[str, Any] | None


class LessonPlanConfigurationAdminService:
    def __init__(self, repository: LessonPlanConfigurationAdminRepositoryProtocol) -> None:
        self._repository = repository

    @staticmethod
    def _require_nonempty(value: str, *, field: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise LessonPlanConfigurationAdminError(f"{field} must not be empty")
        return normalized

    def create_profile_with_initial_draft(
        self,
        *,
        profile_code: str,
        profile_name: str,
        configuration_payload: Mapping[str, Any],
        subject_ref: str = "",
        component_ref: str = "",
        change_note: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self._repository.create_profile(
            profile_code=self._require_nonempty(profile_code, field="profile_code"),
            profile_name=self._require_nonempty(profile_name, field="profile_name"),
            subject_ref=subject_ref,
            component_ref=component_ref,
        )
        profile_id = str(profile.get("profile_id") or "")
        if not profile_id:
            raise LessonPlanConfigurationAdminError(
                "created profile does not contain profile_id"
            )
        version = self._repository.create_draft_version(
            profile_id=profile_id,
            version_number=1,
            configuration_payload=configuration_payload,
            change_note=change_note,
        )
        return profile, version

    def create_next_draft_version(
        self,
        *,
        profile_id: str,
        configuration_payload: Mapping[str, Any],
        change_note: str | None = None,
    ) -> dict[str, Any]:
        profile = self._repository.get_profile(profile_id=profile_id)
        if profile is None:
            raise LessonPlanConfigurationAdminError(f"profile not found: {profile_id}")
        versions = self._repository.list_versions(profile_id=profile_id)
        next_number = max(
            (int(row.get("version_number") or 0) for row in versions),
            default=0,
        ) + 1
        return self._repository.create_draft_version(
            profile_id=profile_id,
            version_number=next_number,
            configuration_payload=configuration_payload,
            change_note=change_note,
        )

    def update_draft(
        self,
        *,
        configuration_version_id: str,
        configuration_payload: Mapping[str, Any],
        change_note: str | None = None,
    ) -> dict[str, Any]:
        version = self._repository.get_version(
            configuration_version_id=configuration_version_id
        )
        if version is None:
            raise LessonPlanConfigurationAdminError(
                f"version not found: {configuration_version_id}"
            )
        if version.get("version_status") != "DRAFT":
            raise LessonPlanConfigurationAdminError(
                "only DRAFT versions may be edited"
            )
        return self._repository.update_draft_version(
            configuration_version_id=configuration_version_id,
            configuration_payload=configuration_payload,
            change_note=change_note,
        )

    def publish(self, *, configuration_version_id: str) -> dict[str, Any]:
        version = self._repository.get_version(
            configuration_version_id=configuration_version_id
        )
        if version is None:
            raise LessonPlanConfigurationAdminError(
                f"version not found: {configuration_version_id}"
            )
        if version.get("version_status") != "DRAFT":
            raise LessonPlanConfigurationAdminError(
                "only DRAFT versions may be published"
            )
        return self._repository.publish_version(
            configuration_version_id=configuration_version_id
        )

    def delete_disposable_profile(self, *, profile_id: str) -> None:
        normalized_profile_id = str(profile_id or "").strip()
        if not normalized_profile_id:
            raise LessonPlanConfigurationAdminError(
                "profile_id must not be empty."
            )

        profile = self._repository.get_profile(
            profile_id=normalized_profile_id
        )
        if profile is None:
            return

        code = str(profile.get("profile_code") or "")
        subject_ref = str(profile.get("subject_ref") or "")
        component_ref = str(profile.get("component_ref") or "")

        if not (
            code.startswith("__SMOKE_C6A")
            and subject_ref.startswith("__SMOKE_C6A")
            and component_ref.startswith("__SMOKE_C6A")
        ):
            raise LessonPlanConfigurationAdminError(
                "Cleanup is restricted to isolated __SMOKE_C6A* profiles."
            )

        self._repository.delete_profile(
            profile_id=normalized_profile_id
        )

    def activate_published_version(
        self,
        *,
        profile_id: str,
        configuration_version_id: str,
        retire_previous: bool = False,
    ) -> LessonPlanConfigurationActivationResult:
        profile = self._repository.get_profile(profile_id=profile_id)
        if profile is None:
            raise LessonPlanConfigurationAdminError(f"profile not found: {profile_id}")

        version = self._repository.get_version(
            configuration_version_id=configuration_version_id
        )
        if version is None:
            raise LessonPlanConfigurationAdminError(
                f"version not found: {configuration_version_id}"
            )
        if str(version.get("profile_id") or "") != profile_id:
            raise LessonPlanConfigurationAdminError(
                "version does not belong to profile"
            )
        if version.get("version_status") != "PUBLISHED":
            raise LessonPlanConfigurationAdminError(
                "only PUBLISHED versions may become current"
            )

        previous_id = profile.get("current_version_id")

        updated_profile = self._repository.set_current_version(
            profile_id=profile_id,
            configuration_version_id=configuration_version_id,
            activate_profile=True,
        )

        retired_previous = None
        if retire_previous and previous_id and str(previous_id) != configuration_version_id:
            previous = self._repository.get_version(
                configuration_version_id=str(previous_id)
            )
            if previous and previous.get("version_status") == "PUBLISHED":
                retired_previous = self._repository.retire_version(
                    configuration_version_id=str(previous_id)
                )

        return LessonPlanConfigurationActivationResult(
            profile=updated_profile,
            current_version=version,
            retired_previous_version=retired_previous,
        )
