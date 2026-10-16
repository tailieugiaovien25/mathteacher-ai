from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable


class KnowledgeTarget(str, Enum):
    LOCAL = "local"
    NOTEBOOKLM = "notebooklm"


@dataclass(frozen=True)
class KnowledgeDocument:
    document_id: str
    title: str
    file_name: str
    mime_type: str
    storage_provider: str
    storage_file_id: str
    source_version: str = "1"
    tags: tuple[str, ...] = ()
    targets: tuple[KnowledgeTarget, ...] = (KnowledgeTarget.LOCAL,)
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if not self.document_id.strip():
            raise ValueError("document_id is required")
        if not self.title.strip():
            raise ValueError("title is required")
        if not self.file_name.strip():
            raise ValueError("file_name is required")
        if not self.storage_file_id.strip():
            raise ValueError("storage_file_id is required")
        if not self.source_version.strip():
            raise ValueError("source_version is required")


class SharedKnowledgeLibrary:
    """Shared layer above the existing TeacherDocumentCatalog.

    The library owns knowledge metadata and synchronization intent.
    It does not replace the existing document repository or call
    external providers directly.
    """

    def __init__(self) -> None:
        self._documents: dict[str, KnowledgeDocument] = {}

    def register(
        self,
        document: KnowledgeDocument,
    ) -> KnowledgeDocument:
        self._documents[document.document_id] = document
        return document

    def get(self, document_id: str) -> KnowledgeDocument | None:
        return self._documents.get(document_id)

    def remove(self, document_id: str) -> bool:
        return self._documents.pop(document_id, None) is not None

    def list_documents(self) -> tuple[KnowledgeDocument, ...]:
        return tuple(self._documents.values())

    def for_target(
        self,
        target: KnowledgeTarget,
    ) -> tuple[KnowledgeDocument, ...]:
        return tuple(
            document
            for document in self._documents.values()
            if target in document.targets
        )

    def register_many(
        self,
        documents: Iterable[KnowledgeDocument],
    ) -> tuple[KnowledgeDocument, ...]:
        registered = tuple(documents)
        for document in registered:
            self.register(document)
        return registered
