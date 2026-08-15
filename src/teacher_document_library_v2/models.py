"""Stable domain values for a personal teacher document catalog."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID


class DocumentCategory(str, Enum):
    LESSON_PLAN = "lesson_plan"
    EDUCATIONAL_PLAN = "educational_plan"
    TEST_MATRIX = "test_matrix"
    TEST_SPECIFICATION = "test_specification"
    TEST_PAPER = "test_paper"
    MARKING_GUIDE = "marking_guide"


DOCUMENT_CATEGORY_LABELS = {
    DocumentCategory.LESSON_PLAN: "Giáo án",
    DocumentCategory.EDUCATIONAL_PLAN: "Kế hoạch giáo dục",
    DocumentCategory.TEST_MATRIX: "Ma trận",
    DocumentCategory.TEST_SPECIFICATION: "Bản đặc tả",
    DocumentCategory.TEST_PAPER: "Đề kiểm tra",
    DocumentCategory.MARKING_GUIDE: "Hướng dẫn chấm",
}


def _required_text(value: str, field_name: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(normalized) > maximum:
        raise ValueError(f"{field_name} must not exceed {maximum} characters")
    return normalized


def _optional_text(value: str | None, field_name: str, maximum: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")
    normalized = " ".join(value.split())
    if not normalized:
        return None
    if len(normalized) > maximum:
        raise ValueError(f"{field_name} must not exceed {maximum} characters")
    return normalized


@dataclass(frozen=True)
class TeacherDocument:
    document_id: str
    title: str
    category: DocumentCategory
    academic_year: str
    subject: str
    grade_level: str
    class_name: str | None
    file_name: str
    mime_type: str
    size_bytes: int
    storage_provider: str
    storage_file_id: str
    web_view_link: str | None = None
    description: str | None = None
    tags: tuple[str, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        try:
            UUID(str(self.document_id))
        except (TypeError, ValueError, AttributeError) as error:
            raise ValueError("document_id must be a UUID") from error
        object.__setattr__(self, "document_id", str(self.document_id).lower())
        object.__setattr__(self, "title", _required_text(self.title, "title", 250))
        if not isinstance(self.category, DocumentCategory):
            try:
                object.__setattr__(self, "category", DocumentCategory(self.category))
            except (TypeError, ValueError) as error:
                raise ValueError("category is not supported") from error
        object.__setattr__(self, "academic_year", _required_text(self.academic_year, "academic_year", 30))
        object.__setattr__(self, "subject", _required_text(self.subject, "subject", 100))
        object.__setattr__(self, "grade_level", _required_text(self.grade_level, "grade_level", 50))
        object.__setattr__(self, "class_name", _optional_text(self.class_name, "class_name", 100))
        object.__setattr__(self, "file_name", _required_text(self.file_name, "file_name", 255))
        object.__setattr__(self, "mime_type", _required_text(self.mime_type, "mime_type", 150))
        if not isinstance(self.size_bytes, int) or isinstance(self.size_bytes, bool) or self.size_bytes < 0:
            raise ValueError("size_bytes must be a non-negative integer")
        object.__setattr__(self, "storage_provider", _required_text(self.storage_provider, "storage_provider", 50))
        object.__setattr__(self, "storage_file_id", _required_text(self.storage_file_id, "storage_file_id", 500))
        object.__setattr__(self, "web_view_link", _optional_text(self.web_view_link, "web_view_link", 2000))
        object.__setattr__(self, "description", _optional_text(self.description, "description", 2000))
        if not isinstance(self.tags, tuple):
            raise TypeError("tags must be a tuple")
        normalized_tags = tuple(
            dict.fromkeys(_required_text(tag, "tag", 100) for tag in self.tags)
        )
        object.__setattr__(self, "tags", normalized_tags)
        for name in ("created_at", "updated_at"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, datetime):
                raise TypeError(f"{name} must be a datetime or None")
            if value is not None and value.tzinfo is None:
                object.__setattr__(self, name, value.replace(tzinfo=timezone.utc))

    @property
    def category_label(self) -> str:
        return DOCUMENT_CATEGORY_LABELS[self.category]

    def with_timestamps(self) -> "TeacherDocument":
        now = datetime.now(timezone.utc)
        return TeacherDocument(
            **{
                **self.__dict__,
                "created_at": self.created_at or now,
                "updated_at": now,
            }
        )
