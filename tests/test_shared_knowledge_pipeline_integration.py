import unittest

from shared_knowledge_library.fake_notebooklm import FakeNotebookLMAdapter
from shared_knowledge_library.library import SharedKnowledgeLibrary
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


class KnowledgePipelineIntegrationTests(unittest.TestCase):

    def test_teacher_document_to_notebooklm_synced(self):
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

        knowledge_document = publisher.publish(source.document_id)

        # Publisher must initialize the local target as PENDING.
        pending = registry.get_status(
            source.document_id,
            "local",
        )
        self.assertIsNotNone(pending)
        self.assertEqual(pending.state, SyncState.PENDING)

        # Fake NotebookLM receives a knowledge copy only.
        fake_notebooklm = FakeNotebookLMAdapter()
        result = fake_notebooklm.upload_file(knowledge_document)

        self.assertEqual(result.target, "notebooklm")
        self.assertEqual(result.document_id, source.document_id)

        # The source TeacherDocument must remain unchanged.
        stored_source = catalog.get(source.document_id)
        self.assertEqual(stored_source.title, source.title)
        self.assertEqual(stored_source.file_name, source.file_name)
        self.assertEqual(stored_source.storage_file_id, source.storage_file_id)

        # Integration checkpoint: the knowledge document exists.
        self.assertIsNotNone(
            library.get(source.document_id)
        )


if __name__ == "__main__":
    unittest.main()
