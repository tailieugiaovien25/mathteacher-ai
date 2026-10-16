import unittest

from shared_knowledge_library.library import KnowledgeDocument
from shared_knowledge_library.sync_executor import LocalKnowledgeSyncExecutor
from shared_knowledge_library.sync_status import KnowledgeSyncRegistry, SyncState


class SyncExecutorTests(unittest.TestCase):

    def setUp(self):
        self.registry = KnowledgeSyncRegistry()
        self.executor = LocalKnowledgeSyncExecutor(self.registry)

        self.document = KnowledgeDocument(
            document_id="550e8400-e29b-41d4-a716-446655440000",
            title="Toán 6",
            file_name="toan6.docx",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            storage_provider="local",
            storage_file_id="storage-test-001",
        )

    def test_local_sync_changes_pending_to_synced(self):
        status = self.executor.sync(
            self.document,
            "local",
            succeed=True,
        )

        self.assertEqual(status.state, SyncState.SYNCED)

        stored = self.registry.get_status(
            self.document.document_id,
            "local",
        )
        self.assertEqual(stored.state, SyncState.SYNCED)

    def test_local_sync_failure_changes_pending_to_failed(self):
        status = self.executor.sync(
            self.document,
            "local",
            succeed=False,
        )

        self.assertEqual(status.state, SyncState.FAILED)
        self.assertEqual(status.message, "Local dry-run sync failed")


if __name__ == "__main__":
    unittest.main()
