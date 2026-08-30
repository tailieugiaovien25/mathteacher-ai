from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .models import ContextFieldKind
from .registry import ContextRegistry, build_default_context_registry


class ContextStateRole(str, Enum):
    CANONICAL = "CANONICAL"
    WIDGET = "WIDGET"
    LEGACY_ALIAS = "LEGACY_ALIAS"
    DERIVED = "DERIVED"
    LOCAL = "LOCAL"


@dataclass(frozen=True, slots=True)
class ContextStateOwnership:
    state_key: str
    canonical_field: str | None
    role: ContextStateRole
    owner: str
    source_page: str
    source_control: str
    authority: str
    description: str = ""


class ContextOwnershipRegistry:
    def __init__(
        self,
        items: Iterable[ContextStateOwnership],
        *,
        context_registry: ContextRegistry | None = None,
    ) -> None:
        self._context_registry = context_registry or build_default_context_registry()
        ordered = tuple(items)
        keys = [item.state_key for item in ordered]
        if len(keys) != len(set(keys)):
            raise ValueError("DUPLICATE_CONTEXT_STATE_KEY")
        for item in ordered:
            if item.canonical_field is not None:
                self._context_registry.get(item.canonical_field)
        self._items = {item.state_key: item for item in ordered}

    def get(self, state_key: str) -> ContextStateOwnership:
        try:
            return self._items[state_key]
        except KeyError as error:
            raise KeyError(f"UNREGISTERED_CONTEXT_STATE_KEY:{state_key}") from error

    def items(self) -> tuple[ContextStateOwnership, ...]:
        return tuple(self._items.values())

    def aliases_for(self, canonical_field: str) -> tuple[ContextStateOwnership, ...]:
        self._context_registry.get(canonical_field)
        return tuple(
            item for item in self._items.values()
            if item.canonical_field == canonical_field
        )

    def competing_owners(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        findings = []
        by_field: dict[str, list[ContextStateOwnership]] = {}
        for item in self._items.values():
            if item.canonical_field is None:
                continue
            by_field.setdefault(item.canonical_field, []).append(item)
        for field, items in by_field.items():
            canonical_owners = {
                item.owner for item in items
                if item.role == ContextStateRole.CANONICAL
            }
            if len(canonical_owners) > 1:
                findings.append((field, tuple(sorted(canonical_owners))))
        return tuple(findings)


def build_default_context_ownership_registry() -> ContextOwnershipRegistry:
    # V57-D1: metadata only. No session-state writes and no business-flow changes.
    return ContextOwnershipRegistry(
        (
            ContextStateOwnership(
                "portal_user_id", "user_id", ContextStateRole.LEGACY_ALIAS,
                "AUTHENTICATED_PORTAL_SESSION", "teacher_portal", "authentication",
                "IDENTITY",
            ),
            ContextStateOwnership(
                "global_weekly_active_academic_year", "academic_year",
                ContextStateRole.CANONICAL, "GLOBAL_WEEKLY_CONTEXT",
                "weekly_schedule", "active_academic_year", "ACADEMIC_CALENDAR",
            ),
            ContextStateOwnership(
                "system_weekly_academic_year", "academic_year",
                ContextStateRole.LEGACY_ALIAS, "LBG_FILTER",
                "weekly_schedule", "lbg_academic_year", "ACADEMIC_CALENDAR",
            ),
            ContextStateOwnership(
                "global_weekly_active_week_number", "week_number",
                ContextStateRole.CANONICAL, "GLOBAL_WEEKLY_CONTEXT",
                "weekly_schedule", "active_week", "ACADEMIC_CALENDAR",
            ),
            ContextStateOwnership(
                "standardization_authoring_week_number", "week_number",
                ContextStateRole.WIDGET, "STANDARDIZATION_SELECTOR",
                "weekly_schedule", "standardization_week", "ACADEMIC_CALENDAR",
            ),
            ContextStateOwnership(
                "system_weekly_week_number", "week_number",
                ContextStateRole.LEGACY_ALIAS, "LBG_FILTER",
                "weekly_schedule", "lbg_week", "ACADEMIC_CALENDAR",
            ),
            ContextStateOwnership(
                "lbg_user_week_number", "week_number",
                ContextStateRole.LEGACY_ALIAS, "LBG_FILTER",
                "weekly_schedule", "lbg_user_week", "ACADEMIC_CALENDAR",
            ),
            ContextStateOwnership(
                "standardization_subject_filter", "subject_ref",
                ContextStateRole.WIDGET, "STANDARDIZATION_SELECTOR",
                "weekly_schedule", "standardization_subject", "TEACHING_ASSIGNMENT",
            ),
            ContextStateOwnership(
                "standardization_component_filter", "component_ref",
                ContextStateRole.WIDGET, "STANDARDIZATION_SELECTOR",
                "weekly_schedule", "standardization_component", "TEACHING_ASSIGNMENT",
            ),
            ContextStateOwnership(
                "portal_navigation", None, ContextStateRole.WIDGET,
                "STREAMLIT_WIDGET", "teacher_portal", "portal_navigation",
                "UI_NAVIGATION",
                "Widget-owned navigation value; callers may request navigation, "
                "but must not also supply a competing default after initialization.",
            ),
            ContextStateOwnership(
                "portal_page", None, ContextStateRole.DERIVED,
                "PORTAL_NAVIGATION_RESOLVER", "teacher_portal", "portal_page",
                "UI_NAVIGATION",
            ),
        )
    )
