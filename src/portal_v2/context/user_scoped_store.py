from __future__ import annotations

from .identity import ContextIdentity
from .models import ContextChange, SystemContext
from .registry import build_default_context_registry
from .synchronization_service import ContextSynchronizationService


class UserScopedContextStore:
    def __init__(self) -> None:
        self._contexts: dict[tuple[str, str], SystemContext] = {}
        self._service = ContextSynchronizationService(
            build_default_context_registry()
        )

    @staticmethod
    def _key(identity: ContextIdentity) -> tuple[str, str]:
        return identity.user_id, identity.context_id

    def put(
        self,
        identity: ContextIdentity,
        context: SystemContext,
    ) -> None:
        if str(context.user_id or "") != identity.user_id:
            raise ValueError(
                "context user_id does not match ContextIdentity"
            )
        self._contexts[self._key(identity)] = context

    def get(self, identity: ContextIdentity) -> SystemContext:
        try:
            return self._contexts[self._key(identity)]
        except KeyError as error:
            raise KeyError("context identity not found") from error

    def apply(
        self,
        identity: ContextIdentity,
        change: ContextChange,
    ) -> SystemContext:
        current = self.get(identity)

        if str(current.user_id or "") != identity.user_id:
            raise RuntimeError("cross-user context mutation rejected")

        result = self._service.apply_change(
            current=current,
            change=change,
        )

        updated = result.context
        if str(updated.user_id or "") != identity.user_id:
            raise RuntimeError("cross-user context mutation rejected")

        self._contexts[self._key(identity)] = updated
        return updated
