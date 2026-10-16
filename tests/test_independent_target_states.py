import unittest

from shared_knowledge_library.library import KnowledgeTarget, SharedKnowledgeLibrary
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


class IndependentTargetStateTests(unittest.TestCase):

    def setUp(self):
        repository = FakeRepository()
        self.catalog = TeacherDocumentCatalog(repository)

        self.source = TeacherDocument(
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

        self.catalog.save(self.source)
        self.registry = KnowledgeSyncRegistry()
        self.publisher = TeacherDocumentKnowledgePublisher(
            self.catalog,
            SharedKnowledgeLibrary(),
            self.registry,
        )

        self.document = self.publisher.publish(self.source.document_id)
        self.publisher.initialize_target(
            self.document.document_id,
            KnowledgeTarget.NOTEBOOKLM.value,
        )

    def test_local_synced_does_not_change_notebooklm(self):
        self.registry.set_status(
            self.document.document_id,
            KnowledgeTarget.LOCAL.value,
            SyncState.SYNCED,
        )

        self.assertEqual(
            self.registry.get_status(
                self.document.document_id,
                KnowledgeTarget.LOCAL.value,
            ).state,
            SyncState.SYNCED,
        )
        self.assertEqual(
            self.registry.get_status(
                self.document.document_id,
                KnowledgeTarget.NOTEBOOKLM.value,
            ).state,
            SyncState.PENDING,
        )

    def test_notebooklm_synced_does_not_change_local(self):
        self.registry.set_status(
            self.document.document_id,
            KnowledgeTarget.NOTEBOOKLM.value,
            SyncState.SYNCED,
        )

        self.assertEqual(
            self.registry.get_status(
                self.document.document_id,
                KnowledgeTarget.NOTEBOOKLM.value,
            ).state,
            SyncState.SYNCED,
        )
        self.assertEqual(
            self.registry.get_status(
                self.document.document_id,
                KnowledgeTarget.LOCAL.value,
            ).state,
            SyncState.PENDING,
        )

    def test_failed_target_does_not_change_other_target(self):
        self.registry.set_status(
            self.document.document_id,
            KnowledgeTarget.NOTEBOOKLM.value,
            SyncState.FAILED,
            message="dry-run failure",
        )

        self.assertEqual(
            self.registry.get_status(
                self.document.document_id,
                KnowledgeTarget.NOTEBOOKLM.value,
            ).state,
            SyncState.FAILED,
        )
        self.assertEqual(
            self.registry.get_status(
                self.document.document_id,
                KnowledgeTarget.LOCAL.value,
            ).state,
            SyncState.PENDING,
        )


if __name__ == "__main__":
    unittest.main()
