from __future__ import annotations

from shared_knowledge_library import SharedKnowledgeLibrary
from shared_knowledge_library.service import SharedKnowledgeLibraryService
from teacher_document_library_v2.services import TeacherDocumentCatalog


class TeacherDocumentKnowledgeBridge:
    """Expose TeacherDocumentCatalog documents to shared knowledge.

    Existing catalog behavior remains unchanged.
    """

    def __init__(
        self,
        catalog: TeacherDocumentCatalog,
        library: SharedKnowledgeLibrary,
    ) -> None:
        self._service = SharedKnowledgeLibraryService(catalog, library)

    def publish(self, document_id: str):
        return self._service.register_document(document_id)

    def publish_many(self, document_ids: tuple[str, ...]):
        return tuple(
            self.publish(document_id)
            for document_id in document_ids
        )
