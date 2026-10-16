import unittest

from shared_knowledge_library import SharedKnowledgeLibrary
from shared_knowledge_library.sync_status import KnowledgeSyncRegistry, SyncState
from shared_knowledge_library.publisher import TeacherDocumentKnowledgePublisher
from teacher_document_library_v2.models import DocumentCategory, TeacherDocument
from teacher_document_library_v2.services import TeacherDocumentCatalog


class FakeRepository:
    def __init__(self):
        self.documents = {}

    def save(self, document):
        self.documents[document.document_id] = document

    def get(self, document_id):
        return self.documents.get(document_id)


class PublisherTests(unittest.TestCase):

    def test_publish_initializes_pending_status(self):
        repository = FakeRepository()
        catalog = TeacherDocumentCatalog(repository)

        document = TeacherDocument(
            document_id="550e8400-e29b-41d4-a716-446655440000",
            title="Toán THCS",
            category=list(DocumentCategory)[0],
            academic_year="2026-2027",
            subject="Toán",
            grade_level="7",
            class_name=None,
            file_name="toan7.pdf",
            mime_type="application/pdf",
            size_bytes=100,
            storage_provider="local",
            storage_file_id="storage-test-001",
        )

        catalog.save(document)

        library = SharedKnowledgeLibrary()
        registry = KnowledgeSyncRegistry()

        publisher = TeacherDocumentKnowledgePublisher(
            catalog,
            library,
            registry,
        )

        result = publisher.publish("550e8400-e29b-41d4-a716-446655440000")

        self.assertEqual(result.document_id, "550e8400-e29b-41d4-a716-446655440000")

        status = registry.get_status(
            "550e8400-e29b-41d4-a716-446655440000",
            "local",
        )

        self.assertIsNotNone(status)
        self.assertEqual(status.state, SyncState.PENDING)

        source = catalog.get("550e8400-e29b-41d4-a716-446655440000")
        self.assertEqual(source.title, "Toán THCS")


if __name__ == "__main__":
    unittest.main()
