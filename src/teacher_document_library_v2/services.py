"""Storage-independent search and catalog operations."""

from __future__ import annotations

from dataclasses import dataclass

from teacher_document_library_v2.models import DocumentCategory, TeacherDocument
from teacher_document_library_v2.repositories import TeacherDocumentRepository


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
