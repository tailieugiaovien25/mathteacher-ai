from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from portal_v2.context.models import ContextChange, SystemContext
from portal_v2.context.registry import build_default_context_registry
from portal_v2.context.synchronization_service import ContextSynchronizationService


_RUNTIME_FIELDS = frozenset(
    {
        "subject_ref",
        "component_ref",
        "grade",
        "class_id",
    }
)


@dataclass(frozen=True)
class RuntimeContextBridgeOutcome:
    context: SystemContext
    changed_field: str
    invalidated_fields: tuple[str, ...]


def apply_runtime_context_change(
    *,
    current: SystemContext,
    field: str,
    value: Any,
    source_page: str,
    source_control: str,
    occurred_at,
) -> RuntimeContextBridgeOutcome:
    if field not in _RUNTIME_FIELDS:
        raise ValueError(f"UNSUPPORTED_RUNTIME_CONTEXT_FIELD:{field}")

    registry = build_default_context_registry()
    service = ContextSynchronizationService(registry)
    result = service.apply_change(
        current=current,
        change=ContextChange(
            field=field,
            value=value,
            source_page=source_page,
            source_control=source_control,
            occurred_at=occurred_at,
        ),
    )

    before = current
    after = result.context
    invalidated = tuple(
        name
        for name in registry.downstream_of(field)
        if getattr(before, name, None) is not None
        and getattr(after, name, None) is None
    )
    return RuntimeContextBridgeOutcome(
        context=after,
        changed_field=field,
        invalidated_fields=invalidated,
    )


def apply_runtime_context_bundle(
    *,
    current: SystemContext,
    values: dict[str, Any],
    source_page: str,
    source_control: str,
    occurred_at,
) -> RuntimeContextBridgeOutcome:
    context = current
    invalidated: list[str] = []
    changed_field = ""

    # Dependency order is deliberate. A parent change invalidates its
    # descendants before a valid descendant is explicitly republished.
    for field in ("subject_ref", "component_ref", "grade", "class_id"):
        if field not in values:
            continue
        outcome = apply_runtime_context_change(
            current=context,
            field=field,
            value=values[field],
            source_page=source_page,
            source_control=source_control,
            occurred_at=occurred_at,
        )
        context = outcome.context
        changed_field = field
        for item in outcome.invalidated_fields:
            if item not in invalidated:
                invalidated.append(item)

    return RuntimeContextBridgeOutcome(
        context=context,
        changed_field=changed_field,
        invalidated_fields=tuple(invalidated),
    )
