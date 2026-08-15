import pytest

from teacher_document_library_v2 import (
    DocumentCategory,
    DocumentUploadMetadata,
    StoredDocumentFile,
    TeacherDocumentCatalog,
    TeacherDocumentUploadService,
)


class MemoryRepository:
    def __init__(self, *, fail_save=False):
        self.rows = {}
        self.fail_save = fail_save

    def save(self, document):
        if self.fail_save:
            raise RuntimeError("metadata unavailable")
        self.rows[document.document_id] = document
        return document

    def get(self, document_id):
        return self.rows.get(document_id)

    def list_all(self):
        return tuple(self.rows.values())

    def delete(self, document_id):
        return self.rows.pop(document_id, None) is not None


class MemoryStorage:
    def __init__(self, *, fail_delete=False):
        self.uploaded = []
        self.deleted = []
        self.fail_delete = fail_delete

    def upload(self, content, file_name, mime_type):
        self.uploaded.append((content, file_name, mime_type))
        return StoredDocumentFile(
            provider="google_drive_oauth",
            file_id="drive-123",
            file_name=file_name,
            mime_type=mime_type,
            size_bytes=len(content),
            web_view_link="https://drive.google.com/file/d/drive-123/view",
        )

    def delete(self, file_id):
        self.deleted.append(file_id)
        if self.fail_delete:
            raise RuntimeError("cleanup unavailable")
        return True


def metadata():
    return DocumentUploadMetadata(
        title="Giáo án tuần 5",
        category=DocumentCategory.LESSON_PLAN,
        academic_year="2026-2027",
        subject="Toán",
        grade_level="6",
        class_name="6A1",
        tags=("tuần 5",),
    )


def test_upload_registers_provider_neutral_metadata():
    repository = MemoryRepository()
    storage = MemoryStorage()
    service = TeacherDocumentUploadService(TeacherDocumentCatalog(repository), storage)

    document = service.upload(
        content=b"word-file",
        file_name="giao-an.docx",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        metadata=metadata(),
    )

    assert document.storage_provider == "google_drive_oauth"
    assert document.storage_file_id == "drive-123"
    assert document.size_bytes == 9
    assert repository.get(document.document_id) == document


def test_metadata_failure_deletes_uploaded_file_and_preserves_original_error():
    storage = MemoryStorage(fail_delete=True)
    service = TeacherDocumentUploadService(
        TeacherDocumentCatalog(MemoryRepository(fail_save=True)), storage
    )

    with pytest.raises(RuntimeError, match="metadata unavailable"):
        service.upload(
            content=b"pdf",
            file_name="de-kiem-tra.pdf",
            mime_type="application/pdf",
            metadata=metadata(),
        )

    assert storage.deleted == ["drive-123"]


def test_empty_content_is_rejected_before_storage():
    storage = MemoryStorage()
    service = TeacherDocumentUploadService(
        TeacherDocumentCatalog(MemoryRepository()), storage
    )

    with pytest.raises(ValueError, match="content"):
        service.upload(
            content=b"", file_name="empty.pdf", mime_type="application/pdf", metadata=metadata()
        )

    assert storage.uploaded == []
