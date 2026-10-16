import unittest

from shared_knowledge_library.library import (
    KnowledgeTarget,
    SharedKnowledgeLibrary,
)
from shared_knowledge_library.publisher import TeacherDocumentKnowledgePublisher
from shared_knowledge_library.sync_status import KnowledgeSyncRegistry, SyncState
from teacher_document_library_v2.models import DocumentCategory, TeacherDocument
from teacher_document_library_v2.services import TeacherDocumentCatalog


class FakeRepository:
    def __init__(self):
        self.documents = {}

    def save(self, document):
        self.documents[document.document_id] = document

    def get(self, document_id):
        return self.documents.get(document_id)


class TargetSpecificSyncTests(unittest.TestCase):

    def test_targets_have_independent_statuses(self):
        repository = FakeRepository()
        catalog = TeacherDocumentCatalog(repository)

        source = TeacherDocument(
            document_id="550e8400-e29b-41d4-a716-446655440000",
            title="Toán 6",
            category=list(DocumentCategory)[0],
            academic_year="2026-2027",
            subject="Toán",
            grade_level="6",
            class_name=None,
            file_name="toan6.docx",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes=1024,
            storage_provider="local",
            storage_file_id="storage-test-001",
        )

        catalog.save(source)

        library = SharedKnowledgeLibrary()
        registry = KnowledgeSyncRegistry()

        publisher = TeacherDocumentKnowledgePublisher(
            catalog,
            library,
            registry,
        )

        document = publisher.publish(source.document_id)

        local = registry.get_status(
            document.document_id,
            KnowledgeTarget.LOCAL.value,
        )

        self.assertEqual(local.state, SyncState.PENDING)

        notebooklm = publisher.initialize_target(
            document.document_id,
            KnowledgeTarget.NOTEBOOKLM.value,
        )

        self.assertEqual(notebooklm.state, SyncState.PENDING)

        self.assertEqual(
            registry.get_status(
                document.document_id,
                KnowledgeTarget.LOCAL.value,
            ).state,
            SyncState.PENDING,
        )

        self.assertEqual(
            registry.get_status(
                document.document_id,
                KnowledgeTarget.NOTEBOOKLM.value,
            ).state,
            SyncState.PENDING,
        )


if __name__ == "__main__":
    unittest.main()
