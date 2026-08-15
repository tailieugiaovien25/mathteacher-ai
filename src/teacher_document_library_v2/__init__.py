"""Teacher-owned document catalog with storage-independent boundaries."""

from teacher_document_library_v2.models import (
    DOCUMENT_CATEGORY_LABELS,
    DocumentCategory,
    TeacherDocument,
)
from teacher_document_library_v2.repositories import TeacherDocumentRepository
from teacher_document_library_v2.services import (
    DocumentFilter,
    DocumentUploadMetadata,
    TeacherDocumentCatalog,
    TeacherDocumentUploadService,
)
from teacher_document_library_v2.storage import DocumentFileStorage, StoredDocumentFile

__all__ = [
    "DOCUMENT_CATEGORY_LABELS",
    "DocumentCategory",
    "DocumentFilter",
    "DocumentFileStorage",
    "DocumentUploadMetadata",
    "StoredDocumentFile",
    "TeacherDocument",
    "TeacherDocumentCatalog",
    "TeacherDocumentUploadService",
    "TeacherDocumentRepository",
]
