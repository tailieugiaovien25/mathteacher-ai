"""Supabase metadata adapter scoped to one authenticated teacher account."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from teacher_document_library_v2.models import DocumentCategory, TeacherDocument


class SupabaseTeacherDocumentRepository:
    def __init__(self, client: Any, user_id: str, table_name: str = "teacher_documents") -> None:
        self._client = client
        self._user_id = self._required_text(user_id, "user_id")
        self._table_name = self._required_text(table_name, "table_name")

    def save(self, document: TeacherDocument) -> TeacherDocument:
        if not isinstance(document, TeacherDocument):
            raise TypeError("document must be a TeacherDocument")
        row = self._to_row(document)
        response = self._client.table(self._table_name).upsert(
            row, on_conflict="user_id,document_id"
        ).execute()
        rows = self._response_rows(response)
        return self._from_row(rows[0]) if rows else document

    def get(self, document_id: str) -> TeacherDocument | None:
        response = (
            self._client.table(self._table_name)
            .select("*")
            .eq("user_id", self._user_id)
            .eq("document_id", self._required_text(document_id, "document_id"))
            .limit(1)
            .execute()
        )
        rows = self._response_rows(response)
        return self._from_row(rows[0]) if rows else None

    def list_all(self) -> tuple[TeacherDocument, ...]:
        response = (
            self._client.table(self._table_name)
            .select("*")
            .eq("user_id", self._user_id)
            .order("updated_at", desc=True)
            .execute()
        )
        return tuple(self._from_row(row) for row in self._response_rows(response))

    def delete(self, document_id: str) -> bool:
        response = (
            self._client.table(self._table_name)
            .delete()
            .eq("user_id", self._user_id)
            .eq("document_id", self._required_text(document_id, "document_id"))
            .execute()
        )
        return bool(self._response_rows(response))

    def _to_row(self, document: TeacherDocument) -> dict[str, Any]:
        return {
            "user_id": self._user_id,
            "document_id": document.document_id,
            "title": document.title,
            "category": document.category.value,
            "academic_year": document.academic_year,
            "subject": document.subject,
            "grade_level": document.grade_level,
            "class_name": document.class_name,
            "file_name": document.file_name,
            "mime_type": document.mime_type,
            "size_bytes": document.size_bytes,
            "storage_provider": document.storage_provider,
            "storage_file_id": document.storage_file_id,
            "web_view_link": document.web_view_link,
            "description": document.description,
            "tags": list(document.tags),
            "created_at": self._iso(document.created_at),
            "updated_at": self._iso(document.updated_at),
        }

    @staticmethod
    def _from_row(row: dict[str, Any]) -> TeacherDocument:
        return TeacherDocument(
            document_id=row["document_id"],
            title=row["title"],
            category=DocumentCategory(row["category"]),
            academic_year=row["academic_year"],
            subject=row["subject"],
            grade_level=row["grade_level"],
            class_name=row.get("class_name"),
            file_name=row["file_name"],
            mime_type=row["mime_type"],
            size_bytes=row["size_bytes"],
            storage_provider=row["storage_provider"],
            storage_file_id=row["storage_file_id"],
            web_view_link=row.get("web_view_link"),
            description=row.get("description"),
            tags=tuple(row.get("tags") or ()),
            created_at=SupabaseTeacherDocumentRepository._datetime(row.get("created_at")),
            updated_at=SupabaseTeacherDocumentRepository._datetime(row.get("updated_at")),
        )

    @staticmethod
    def _response_rows(response: Any) -> list[dict[str, Any]]:
        rows = getattr(response, "data", None)
        if not isinstance(rows, list):
            raise ValueError("Supabase response does not contain list data")
        return rows

    @staticmethod
    def _required_text(value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must not be empty")
        return value.strip()

    @staticmethod
    def _iso(value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None

    @staticmethod
    def _datetime(value: Any) -> datetime | None:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
