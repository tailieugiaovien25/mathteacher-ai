import unittest

from shared_knowledge_library.fake_notebooklm import FakeNotebookLMAdapter
from shared_knowledge_library.library import KnowledgeDocument
from shared_knowledge_library.sync_status import KnowledgeSyncRegistry, SyncState
from shared_knowledge_library.sync_executor import LocalKnowledgeSyncExecutor


class FakeNotebookLMAdapterTests(unittest.TestCase):

    def setUp(self):
        self.document = KnowledgeDocument(
            document_id="550e8400-e29b-41d4-a716-446655440000",
            title="Toán 6",
            file_name="toan6.docx",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            storage_provider="local",
            storage_file_id="storage-test-001",
        )

    def test_fake_adapter_upload_is_local_only(self):
        result = FakeNotebookLMAdapter().upload_file(self.document)

        self.assertEqual(result.document_id, self.document.document_id)
        self.assertEqual(result.target, "notebooklm")
        self.assertTrue(result.external_id.startswith("fake-notebooklm:"))

    def test_notebooklm_sync_contract(self):
        registry = KnowledgeSyncRegistry()
        executor = LocalKnowledgeSyncExecutor(registry)
        adapter = FakeNotebookLMAdapter()

        result = adapter.upload_file(self.document)

        status = executor.sync(
            self.document,
            result.target,
            succeed=True,
        )

        self.assertEqual(status.state, SyncState.SYNCED)
        self.assertEqual(
            registry.get_status(
                self.document.document_id,
                "notebooklm",
            ).state,
            SyncState.SYNCED,
        )


if __name__ == "__main__":
    unittest.main()
