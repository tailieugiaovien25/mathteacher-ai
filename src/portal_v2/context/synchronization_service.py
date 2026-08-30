# V57-B PHASE 1
from __future__ import annotations

from dataclasses import fields
from datetime import datetime
from typing import Any

from .models import ContextChange, ContextEvent, SynchronizationResult, SystemContext
from .registry import ContextRegistry, build_default_context_registry


class ContextSynchronizationService:
    """Compatibility-first transition service.

    Phase 1 never fabricates timetable/PPCT values. It only applies an
    explicit change and invalidates stale downstream context.
    """

    def __init__(self, registry: ContextRegistry | None = None) -> None:
        self._registry = registry or build_default_context_registry()
        self._model_fields = {item.name for item in fields(SystemContext)}

    @property
    def registry(self) -> ContextRegistry:
        return self._registry

    def apply_change(
        self,
        *,
        current: SystemContext,
        change: ContextChange,
    ) -> SynchronizationResult:
        spec = self._registry.get(change.field)

        if spec.name not in self._model_fields:
            raise ValueError(f"CONTEXT_FIELD_NOT_IN_MODEL:{spec.name}")

        old_value = getattr(current, change.field)
        if old_value == change.value:
            return SynchronizationResult(
                context=current,
                events=(),
                invalidated_fields=(),
            )

        invalidated = self._registry.downstream_of(change.field)
        changes: dict[str, Any] = {
            change.field: change.value,
            "source_page": change.source_page,
            "source_control": change.source_control,
            "context_version": current.context_version + 1,
        }

        for field_name in invalidated:
            if field_name in {"source_page", "source_control", "context_version"}:
                continue
            changes[field_name] = None

        next_context = current.with_values(**changes)
        event = ContextEvent(
            field=change.field,
            old_value=old_value,
            new_value=change.value,
            source_page=change.source_page,
            source_control=change.source_control,
            invalidated_fields=invalidated,
            context_version=next_context.context_version,
            occurred_at=change.occurred_at,
        )

        return SynchronizationResult(
            context=next_context,
            events=(event,),
            invalidated_fields=invalidated,
        )

    def apply_value(
        self,
        *,
        current: SystemContext,
        field: str,
        value: Any,
        source_page: str,
        source_control: str,
        occurred_at: datetime | None = None,
    ) -> SynchronizationResult:
        return self.apply_change(
            current=current,
            change=ContextChange(
                field=field,
                value=value,
                source_page=source_page,
                source_control=source_control,
                occurred_at=occurred_at or datetime.now(),
            ),
        )
