"""Storage-independent search and catalog operations."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from teacher_document_library_v2.models import DocumentCategory, TeacherDocument
from teacher_document_library_v2.repositories import TeacherDocumentRepository
from teacher_document_library_v2.storage import DocumentFileStorage


@dataclass(frozen=True)
class DocumentFilter:
    query: str = ""
    academic_year: str | None = None
    subject: str | None = None
    grade_level: str | None = None
    category: DocumentCategory | None = None


class TeacherDocumentCatalog:
    def __init__(self, repository: TeacherDocumentRepository) -> None:
        self._repository = repository

    def save(self, document: TeacherDocument) -> TeacherDocument:
        return self._repository.save(document.with_timestamps())

    def get(self, document_id: str) -> TeacherDocument | None:
        return self._repository.get(document_id)

    def delete(self, document_id: str) -> bool:
        return self._repository.delete(document_id)

    def search(self, criteria: DocumentFilter | None = None) -> tuple[TeacherDocument, ...]:
        criteria = criteria or DocumentFilter()
        query = criteria.query.strip().casefold()
        matches = []
        for document in self._repository.list_all():
            haystack = " ".join(
                (document.title, document.description or "", *document.tags)
            ).casefold()
            if query and query not in haystack:
                continue
            if criteria.academic_year and document.academic_year != criteria.academic_year:
                continue
            if criteria.subject and document.subject != criteria.subject:
                continue
            if criteria.grade_level and document.grade_level != criteria.grade_level:
                continue
            if criteria.category and document.category != criteria.category:
                continue
            matches.append(document)
        return tuple(
            sorted(matches, key=lambda item: (item.updated_at or item.created_at or datetime_min(), item.title), reverse=True)
        )


def datetime_min():
    from datetime import datetime, timezone

    return datetime.min.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class DocumentUploadMetadata:
    title: str
    category: DocumentCategory
    academic_year: str
    subject: str
    grade_level: str
    class_name: str | None = None
    description: str | None = None
    tags: tuple[str, ...] = ()


class TeacherDocumentUploadService:
    """Upload a file then register metadata, compensating if metadata save fails."""

    def __init__(self, catalog: TeacherDocumentCatalog, storage: DocumentFileStorage) -> None:
        self._catalog = catalog
        self._storage = storage

    def upload(
        self,
        *,
        content: bytes,
        file_name: str,
        mime_type: str,
        metadata: DocumentUploadMetadata,
    ) -> TeacherDocument:
        if not isinstance(content, bytes) or not content:
            raise ValueError("content must not be empty")
        stored = self._storage.upload(content, file_name, mime_type)
        document = TeacherDocument(
            document_id=str(uuid4()),
            title=metadata.title,
            category=metadata.category,
            academic_year=metadata.academic_year,
            subject=metadata.subject,
            grade_level=metadata.grade_level,
            class_name=metadata.class_name,
            file_name=stored.file_name,
            mime_type=stored.mime_type,
            size_bytes=stored.size_bytes,
            storage_provider=stored.provider,
            storage_file_id=stored.file_id,
            web_view_link=stored.web_view_link,
            description=metadata.description,
            tags=metadata.tags,
        )
        try:
            return self._catalog.save(document)
        except Exception:
            try:
                self._storage.delete(stored.file_id)
            except Exception:
                # Preserve the metadata error that triggered compensation.
                pass
            raise
