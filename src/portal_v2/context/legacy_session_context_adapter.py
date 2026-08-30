"""V57-C PHASE 1 compatibility adapter.

Read-only projection of legacy Streamlit session-state into V57-B SystemContext.
"""
from __future__ import annotations
from dataclasses import fields
from typing import Any, Mapping
from .models import SystemContext

LEGACY_CONTEXT_ALIASES = {
    "user_id": ("portal_user_id",),
    "academic_year": ("global_weekly_active_academic_year", "system_weekly_academic_year"),
    "week_number": (
        "global_weekly_active_week_number",
        "standardization_authoring_week_number",
        "system_weekly_week_number",
        "lbg_user_week_number",
    ),
    "subject_ref": ("standardization_subject_filter",),
    "component_ref": ("standardization_component_filter",),
}

def _coerce(field_name: str, value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
    if field_name in {"week_number", "grade", "timetable_period", "curriculum_period"}:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return value

def resolve_legacy_value(session_state: Mapping[str, Any], field_name: str) -> Any:
    for key in LEGACY_CONTEXT_ALIASES.get(field_name, ()):
        if key in session_state:
            value = _coerce(field_name, session_state.get(key))
            if value is not None:
                return value
    return None

def project_system_context(
    session_state: Mapping[str, Any],
    *,
    base_context: SystemContext | None = None,
    source_page: str = "weekly_schedule",
    source_control: str = "legacy_session_projection",
) -> SystemContext:
    base = base_context or SystemContext()
    values = {item.name: getattr(base, item.name) for item in fields(SystemContext)}
    for field_name in LEGACY_CONTEXT_ALIASES:
        value = resolve_legacy_value(session_state, field_name)
        if value is not None:
            values[field_name] = value
    values["source_page"] = source_page
    values["source_control"] = source_control
    return SystemContext(**values)

def registered_legacy_keys() -> frozenset[str]:
    return frozenset(key for aliases in LEGACY_CONTEXT_ALIASES.values() for key in aliases)
