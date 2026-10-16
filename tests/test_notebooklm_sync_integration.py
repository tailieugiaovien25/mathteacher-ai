import unittest

from shared_knowledge_library.library import KnowledgeTarget, SharedKnowledgeLibrary
from shared_knowledge_library.notebooklm_adapter import SharedKnowledgeNotebookLMAdapter
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


class FakeNotebookLMClient:
    def upload_file(self, notebook_id, file_path, display_name, content_type):
        return "fake-notebooklm-upload-001"


class NotebookLMSyncIntegrationTests(unittest.TestCase):

    def test_notebooklm_sync_changes_only_notebooklm_status(self):
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

        # Explicitly enable the NotebookLM target.
        publisher.initialize_target(
            document.document_id,
            KnowledgeTarget.NOTEBOOKLM.value,
        )

        # Both targets start independently.
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

        # NotebookLM adapter uses only the injected fake client.
        adapter = SharedKnowledgeNotebookLMAdapter(
            FakeNotebookLMClient()
        )

        result = adapter.sync(document)

        self.assertEqual(
            result,
            "fake-notebooklm-upload-001",
        )

        # Only NotebookLM becomes SYNCED.
        registry.set_status(
            document.document_id,
            KnowledgeTarget.NOTEBOOKLM.value,
            SyncState.SYNCED,
        )

        self.assertEqual(
            registry.get_status(
                document.document_id,
                KnowledgeTarget.NOTEBOOKLM.value,
            ).state,
            SyncState.SYNCED,
        )

        # LOCAL remains untouched.
        self.assertEqual(
            registry.get_status(
                document.document_id,
                KnowledgeTarget.LOCAL.value,
            ).state,
            SyncState.PENDING,
        )

        # Original TeacherDocument remains untouched.
        stored = catalog.get(source.document_id)

        self.assertEqual(stored.title, source.title)
        self.assertEqual(stored.file_name, source.file_name)
        self.assertEqual(
            stored.storage_file_id,
            source.storage_file_id,
        )


if __name__ == "__main__":
    unittest.main()
