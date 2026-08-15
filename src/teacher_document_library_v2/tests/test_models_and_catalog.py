from datetime import datetime
from uuid import uuid4

import pytest

from teacher_document_library_v2 import (
    DocumentCategory,
    DocumentFilter,
    TeacherDocument,
    TeacherDocumentCatalog,
)


def _document(title="Giáo án Tập hợp", subject="Toán", category=DocumentCategory.LESSON_PLAN):
    return TeacherDocument(
        document_id=str(uuid4()), title=title, category=category,
        academic_year="2026-2027", subject=subject, grade_level="6",
        class_name="6A1", file_name="giao-an.docx",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=1200, storage_provider="google_drive_manual",
        storage_file_id="drive-file-1", description="Bài dạy học kỳ 1",
        tags=("học kỳ 1", "đã chuẩn hóa", "học kỳ 1"),
        created_at=datetime(2026, 8, 15),
    )


class MemoryRepository:
    def __init__(self):
        self.rows = {}

    def save(self, document):
        self.rows[document.document_id] = document
        return document

    def get(self, document_id):
        return self.rows.get(document_id)

    def list_all(self):
        return tuple(self.rows.values())

    def delete(self, document_id):
        return self.rows.pop(document_id, None) is not None


def test_document_normalizes_values_and_tags():
    document = _document()
    assert document.title == "Giáo án Tập hợp"
    assert document.tags == ("học kỳ 1", "đã chuẩn hóa")
    assert document.created_at.tzinfo is not None
    assert document.category_label == "Giáo án"


def test_document_rejects_invalid_identity_and_size():
    with pytest.raises(ValueError, match="UUID"):
        TeacherDocument(**{**_document().__dict__, "document_id": "../bad"})
    with pytest.raises(ValueError, match="size_bytes"):
        TeacherDocument(**{**_document().__dict__, "size_bytes": -1})


def test_catalog_searches_and_filters_without_storage_dependency():
    repository = MemoryRepository()
    catalog = TeacherDocumentCatalog(repository)
    first = catalog.save(_document())
    catalog.save(_document("Ma trận giữa kỳ", "Toán", DocumentCategory.TEST_MATRIX))
    catalog.save(_document("Lesson plan Unit 1", "Tiếng Anh"))

    assert catalog.get(first.document_id) == first
    assert len(catalog.search(DocumentFilter(query="chuẩn hóa"))) == 3
    assert len(catalog.search(DocumentFilter(subject="Toán"))) == 2
    assert len(catalog.search(DocumentFilter(category=DocumentCategory.TEST_MATRIX))) == 1
    assert catalog.delete(first.document_id) is True
