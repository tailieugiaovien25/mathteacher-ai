from __future__ import annotations

from shared_knowledge_library.library import SharedKnowledgeLibrary
from shared_knowledge_library.service import SharedKnowledgeLibraryService
from shared_knowledge_library.sync_status import (
    KnowledgeSyncRegistry,
    SyncState,
)
from teacher_document_library_v2.services import TeacherDocumentCatalog


class TeacherDocumentKnowledgePublisher:
    """Publishes a teacher document and initializes target-specific sync state."""

    def __init__(
        self,
        catalog: TeacherDocumentCatalog,
        library: SharedKnowledgeLibrary,
        sync_registry: KnowledgeSyncRegistry,
    ) -> None:
        self._service = SharedKnowledgeLibraryService(catalog, library)
        self._sync_registry = sync_registry

    def publish(self, document_id: str):
        knowledge_document = self._service.register_document(document_id)

        for target in knowledge_document.targets:
            self._sync_registry.set_status(
                knowledge_document.document_id,
                target.value,
                SyncState.PENDING,
            )

        return knowledge_document

    def initialize_target(
        self,
        document_id: str,
        target: str,
    ):
        return self._sync_registry.set_status(
            document_id,
            target,
            SyncState.PENDING,
        )
