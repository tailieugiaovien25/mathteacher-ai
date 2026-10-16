from __future__ import annotations

from shared_knowledge_library.library import (
    KnowledgeDocument,
    SharedKnowledgeLibrary,
)
from teacher_document_library_v2.services import TeacherDocumentCatalog


class SharedKnowledgeLibraryService:
    """Bridge existing TeacherDocumentCatalog into shared knowledge."""

    def __init__(
        self,
        catalog: TeacherDocumentCatalog,
        library: SharedKnowledgeLibrary,
    ) -> None:
        self.catalog = catalog
        self.library = library

    def register_document(
        self,
        document_id: str,
    ) -> KnowledgeDocument:
        document = self.catalog.get(document_id)

        if document is None:
            raise ValueError(
                f"Teacher document not found: {document_id}"
            )

        knowledge_document = KnowledgeDocument(
            document_id=document.document_id,
            title=document.title,
            file_name=document.file_name,
            mime_type=document.mime_type,
            storage_provider=document.storage_provider,
            storage_file_id=document.storage_file_id,
            tags=document.tags,
        )

        return self.library.register(knowledge_document)
