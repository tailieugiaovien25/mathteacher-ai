"""Repository contract for teacher-owned document metadata."""

from __future__ import annotations

from typing import Protocol

from teacher_document_library_v2.models import TeacherDocument


class TeacherDocumentRepository(Protocol):
    def save(self, document: TeacherDocument) -> TeacherDocument: ...
    def get(self, document_id: str) -> TeacherDocument | None: ...
    def list_all(self) -> tuple[TeacherDocument, ...]: ...
    def delete(self, document_id: str) -> bool: ...
