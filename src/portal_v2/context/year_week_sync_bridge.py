from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from portal_v2.context.models import ContextChange, SystemContext
from portal_v2.context.synchronization_service import ContextSynchronizationService

V57F2C4_CANONICAL_YEAR_WEEK_BRIDGE = True

ACADEMIC_YEAR_ALIAS_KEYS = (
    "global_weekly_active_academic_year",
    "system_weekly_academic_year",
)

WEEK_NUMBER_ALIAS_KEYS = (
    "global_weekly_active_week_number",
    "standardization_authoring_week_number",
    "system_weekly_week_number",
    "lbg_user_week_number",
)

YEAR_WEEK_FIELDS = frozenset({"academic_year", "week_number"})

@dataclass(frozen=True)
class YearWeekSynchronizationOutcome:
    context: SystemContext
    projection: Mapping[str, object]
    raw_result: Any

def project_year_week_aliases(context: SystemContext) -> dict[str, object]:
    """Build legacy/widget projection values without mutating external state."""
    projection: dict[str, object] = {}
    for key in ACADEMIC_YEAR_ALIAS_KEYS:
        projection[key] = context.academic_year
    for key in WEEK_NUMBER_ALIAS_KEYS:
        projection[key] = context.week_number
    return projection

def _extract_context(result: Any) -> SystemContext:
    if isinstance(result, SystemContext):
        return result
    for attribute in ("context", "updated_context", "system_context", "current"):
        candidate = getattr(result, attribute, None)
        if isinstance(candidate, SystemContext):
            return candidate
    raise TypeError("Synchronization result does not expose a SystemContext")

class YearWeekContextBridge:
    """
    Canonical bridge for academic_year/week_number.

    The bridge never writes UI session state. It emits ContextChange to
    ContextSynchronizationService and returns a projection that callers may
    publish to legacy/widget aliases during migration.
    """

    def __init__(self, *, service: ContextSynchronizationService) -> None:
        self._service = service

    def apply_change(
        self,
        *,
        current: SystemContext,
        field: str,
        value: object,
        source_page: str,
        source_control: str,
    ) -> YearWeekSynchronizationOutcome:
        if field not in YEAR_WEEK_FIELDS:
            raise ValueError(f"Unsupported year/week context field: {field}")
        change = ContextChange(
            field=field,
            value=value,
            source_page=source_page,
            source_control=source_control,
            occurred_at=datetime.now(timezone.utc),
        )
        raw_result = self._service.apply_change(current=current, change=change)
        context = _extract_context(raw_result)
        return YearWeekSynchronizationOutcome(
            context=context,
            projection=project_year_week_aliases(context),
            raw_result=raw_result,
        )
