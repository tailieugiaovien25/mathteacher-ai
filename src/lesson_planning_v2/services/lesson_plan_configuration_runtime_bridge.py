from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping

from lesson_planning_v2.adapters.supabase_lesson_plan_configuration_repository import (
    SupabaseLessonPlanConfigurationRepository,
)
from lesson_planning_v2.services.lesson_plan_configuration_service import (
    LessonPlanConfigurationService,
)


ADMIN_RUNTIME_PAYLOAD_KEY = "lesson_plan_admin_runtime_configuration_payload"
ADMIN_RUNTIME_SOURCE_KEY = "lesson_plan_admin_runtime_configuration_source"
ADMIN_RUNTIME_ERROR_KEY = "lesson_plan_admin_runtime_configuration_error"

_DATE_POLICY_KEY_MAP = {
    "drafting_before_monday_enabled":
        "standardization_drafting_before_monday_enabled",
    "drafting_before_monday_days":
        "standardization_drafting_before_monday_days",
    "approval_before_monday_enabled":
        "standardization_approval_before_monday_enabled",
    "approval_before_monday_days":
        "standardization_approval_before_monday_days",
}

_DIRECT_DATE_POLICY_KEYS = frozenset(_DATE_POLICY_KEY_MAP.values())

_TEMPLATE_PROFILE_STATE_KEYS = (
    "lesson_plan_template_profile",
    "subject_lesson_plan_profile",
)

_APPROVAL_POLICY_KEY_MAP = {
    "approval_label": "lesson_plan_admin_approval_label",
    "alignment": "lesson_plan_admin_approval_alignment",
    "approval_offset_days": "standardization_approval_before_monday_days",
}


def _project_template_profile(
    *,
    template_profile: Mapping[str, Any],
    session_state: MutableMapping[str, Any],
) -> None:
    normalized = dict(template_profile)
    session_state["lesson_plan_admin_template_profile"] = normalized
    for state_key in _TEMPLATE_PROFILE_STATE_KEYS:
        session_state[state_key] = normalized


def _project_approval_policy(
    *,
    approval_policy: Mapping[str, Any],
    session_state: MutableMapping[str, Any],
) -> None:
    normalized = dict(approval_policy)
    session_state["lesson_plan_admin_approval_policy"] = normalized
    for source_key, target_key in _APPROVAL_POLICY_KEY_MAP.items():
        if source_key in normalized:
            session_state[target_key] = normalized[source_key]



@dataclass(frozen=True)
class AdminRuntimeProjectionResult:
    applied: bool
    source: str
    payload: Mapping[str, Any]


def _clean_ref(value: Any) -> str:
    return str(value or "").strip()


def _runtime_subject_ref(session_state: Mapping[str, Any]) -> str:
    candidates = (
        session_state.get("standardization_subject_filter"),
        session_state.get("lesson_authoring_subject_ref"),
        session_state.get("subject_ref"),
    )
    for value in candidates:
        cleaned = _clean_ref(value)
        if cleaned:
            return cleaned
    return ""


def _runtime_component_ref(session_state: Mapping[str, Any]) -> str:
    candidates = (
        session_state.get("standardization_component_filter"),
        session_state.get("lesson_authoring_component_ref"),
        session_state.get("component_ref"),
    )
    for value in candidates:
        cleaned = _clean_ref(value)
        if cleaned:
            return cleaned
    return ""


def project_admin_payload_to_standardization_state(
    *,
    payload: Mapping[str, Any] | None,
    session_state: MutableMapping[str, Any],
) -> None:
    normalized = dict(payload or {})
    session_state[ADMIN_RUNTIME_PAYLOAD_KEY] = normalized

    date_policy = normalized.get("date_policy")
    if isinstance(date_policy, Mapping):
        for source_key, target_key in _DATE_POLICY_KEY_MAP.items():
            if source_key in date_policy:
                session_state[target_key] = date_policy[source_key]

        for direct_key in _DIRECT_DATE_POLICY_KEYS:
            if direct_key in date_policy:
                session_state[direct_key] = date_policy[direct_key]

    template_profile = normalized.get("template_profile")
    if isinstance(template_profile, Mapping):
        _project_template_profile(
            template_profile=template_profile,
            session_state=session_state,
        )

    approval_policy = normalized.get("approval_policy")
    if isinstance(approval_policy, Mapping):
        _project_approval_policy(
            approval_policy=approval_policy,
            session_state=session_state,
        )


def apply_active_admin_lesson_plan_configuration(
    *,
    client: Any,
    session_state: MutableMapping[str, Any],
) -> AdminRuntimeProjectionResult:
    subject_ref = _runtime_subject_ref(session_state)
    component_ref = _runtime_component_ref(session_state)

    if client is None or not subject_ref:
        session_state.pop(ADMIN_RUNTIME_ERROR_KEY, None)
        return AdminRuntimeProjectionResult(
            applied=False,
            source="existing_runtime_default",
            payload={},
        )

    try:
        repository = SupabaseLessonPlanConfigurationRepository(client)
        service = LessonPlanConfigurationService(repository)
        resolved = service.resolve(
            subject_ref=subject_ref,
            component_ref=component_ref or None,
            fallback_payload={},
        )
    except Exception as error:
        session_state[ADMIN_RUNTIME_ERROR_KEY] = str(error)
        return AdminRuntimeProjectionResult(
            applied=False,
            source="existing_runtime_default",
            payload={},
        )

    if resolved.snapshot is None:
        session_state.pop(ADMIN_RUNTIME_ERROR_KEY, None)
        session_state[ADMIN_RUNTIME_SOURCE_KEY] = "existing_runtime_default"
        return AdminRuntimeProjectionResult(
            applied=False,
            source="existing_runtime_default",
            payload={},
        )

    payload = dict(resolved.configuration_payload)
    project_admin_payload_to_standardization_state(
        payload=payload,
        session_state=session_state,
    )
    session_state[ADMIN_RUNTIME_SOURCE_KEY] = (
        "admin_active:"
        + str(resolved.snapshot.profile_id)
        + ":"
        + str(resolved.snapshot.configuration_version_id)
    )
    session_state.pop(ADMIN_RUNTIME_ERROR_KEY, None)

    return AdminRuntimeProjectionResult(
        applied=True,
        source=session_state[ADMIN_RUNTIME_SOURCE_KEY],
        payload=payload,
    )
