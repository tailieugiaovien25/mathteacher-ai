from __future__ import annotations

from shared_knowledge_library.library import KnowledgeDocument
from shared_knowledge_library.sync_status import (
    KnowledgeSyncRegistry,
    SyncState,
)


class LocalKnowledgeSyncExecutor:
    """Local dry-run executor for shared knowledge synchronization.

    Does not modify the source TeacherDocument and does not call
    external providers.
    """

    def __init__(self, sync_registry: KnowledgeSyncRegistry) -> None:
        self._sync_registry = sync_registry

    def sync(
        self,
        document: KnowledgeDocument,
        target: str,
        *,
        succeed: bool = True,
    ):
        if succeed:
            return self._sync_registry.set_status(
                document.document_id,
                target,
                SyncState.SYNCED,
                message="Local dry-run sync completed",
            )

        return self._sync_registry.set_status(
            document.document_id,
            target,
            SyncState.FAILED,
            message="Local dry-run sync failed",
        )
