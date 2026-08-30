from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, MutableMapping
from uuid import uuid4

from .identity import ContextIdentity
from .legacy_session_context_adapter import project_system_context
from .models import ContextChange, SystemContext
from .user_scoped_store import UserScopedContextStore
from .year_week_sync_bridge import project_year_week_aliases


V57F2C5D_SESSION_SCOPED_CANONICAL_HOLDER = True

_STORE_KEY = "_v57_system_context_store"
_CONTEXT_ID_KEY = "_v57_system_context_id"

YEAR_WEEK_FIELDS = frozenset({"academic_year", "week_number"})


def _identity(
    session_state: MutableMapping[str, Any],
    *,
    user_id: str,
) -> ContextIdentity:
    context_id = session_state.get(_CONTEXT_ID_KEY)
    if not context_id:
        context_id = f"streamlit-{uuid4()}"
        session_state[_CONTEXT_ID_KEY] = context_id
    return ContextIdentity(
        user_id=str(user_id),
        context_id=str(context_id),
    )


def _store(
    session_state: MutableMapping[str, Any],
) -> UserScopedContextStore:
    store = session_state.get(_STORE_KEY)
    if isinstance(store, UserScopedContextStore):
        return store
    store = UserScopedContextStore()
    session_state[_STORE_KEY] = store
    return store


def ensure_canonical_context(
    session_state: MutableMapping[str, Any],
    *,
    user_id: str,
    source_page: str,
    source_control: str = "legacy_bootstrap",
) -> tuple[ContextIdentity, SystemContext]:
    identity = _identity(session_state, user_id=str(user_id))
    store = _store(session_state)

    try:
        current = store.get(identity)
    except KeyError:
        projected = project_system_context(
            session_state,
            source_page=source_page,
            source_control=source_control,
        )
        current = projected.with_values(user_id=str(user_id))
        store.put(identity, current)

    if str(current.user_id or "") != str(user_id):
        raise RuntimeError("cross-user canonical context rejected")

    return identity, current


def publish_year_week_projection(
    session_state: MutableMapping[str, Any],
    *,
    context: SystemContext,
) -> dict[str, object]:
    projection = project_year_week_aliases(context)
    for key, value in projection.items():
        if value is None:
            session_state.pop(key, None)
        else:
            session_state[key] = value
    return projection


def apply_canonical_year_week_change(
    session_state: MutableMapping[str, Any],
    *,
    user_id: str,
    field: str,
    value: object,
    source_page: str,
    source_control: str,
) -> SystemContext:
    if field not in YEAR_WEEK_FIELDS:
        raise ValueError(f"Unsupported canonical year/week field: {field}")

    identity, _ = ensure_canonical_context(
        session_state,
        user_id=str(user_id),
        source_page=source_page,
    )

    change = ContextChange(
        field=field,
        value=value,
        source_page=source_page,
        source_control=source_control,
        occurred_at=datetime.now(timezone.utc),
    )

    store = _store(session_state)
    updated = store.apply(identity, change)

    if str(updated.user_id or "") != str(user_id):
        raise RuntimeError("cross-user canonical context rejected")

    publish_year_week_projection(
        session_state,
        context=updated,
    )
    return updated


def get_canonical_context(
    session_state: MutableMapping[str, Any],
    *,
    user_id: str,
    source_page: str,
) -> SystemContext:
    _, current = ensure_canonical_context(
        session_state,
        user_id=str(user_id),
        source_page=source_page,
    )
    return current
