# V57-B PHASE 1
"""System-wide context synchronization core.

V57-B Phase 1 is additive and compatibility-first. It does not replace
existing Streamlit session state or persist context to the database.
"""

from .models import (
    ContextChange,
    ContextEvent,
    ContextFieldKind,
    SynchronizationResult,
    SystemContext,
)
from .registry import ContextFieldSpec, ContextRegistry, build_default_context_registry
from .synchronization_service import ContextSynchronizationService

__all__ = [
    "ContextChange",
    "ContextEvent",
    "ContextFieldKind",
    "ContextFieldSpec",
    "ContextRegistry",
    "ContextSynchronizationService",
    "SynchronizationResult",
    "SystemContext",
    "build_default_context_registry",
]
