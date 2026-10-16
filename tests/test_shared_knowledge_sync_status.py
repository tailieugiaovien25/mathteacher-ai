import unittest

from shared_knowledge_library.sync_status import (
    KnowledgeSyncRegistry,
    SyncState,
)


class KnowledgeSyncRegistryTests(unittest.TestCase):

    def test_pending_status(self):
        registry = KnowledgeSyncRegistry()

        status = registry.set_status(
            "doc-001",
            "local",
            SyncState.PENDING,
        )

        self.assertEqual(status.state, SyncState.PENDING)
        self.assertEqual(registry.get_status("doc-001", "local"), status)

    def test_synced_status(self):
        registry = KnowledgeSyncRegistry()

        status = registry.set_status(
            "doc-001",
            "notebooklm",
            SyncState.SYNCED,
        )

        self.assertEqual(status.state, SyncState.SYNCED)

    def test_failed_status_keeps_message(self):
        registry = KnowledgeSyncRegistry()

        status = registry.set_status(
            "doc-001",
            "notebooklm",
            SyncState.FAILED,
            "adapter unavailable",
        )

        self.assertEqual(status.state, SyncState.FAILED)
        self.assertEqual(status.message, "adapter unavailable")

    def test_source_document_is_not_touched(self):
        registry = KnowledgeSyncRegistry()

        registry.set_status(
            "doc-001",
            "local",
            SyncState.SYNCED,
        )

        self.assertEqual(
            registry.get_status("doc-001", "local").document_id,
            "doc-001",
        )


if __name__ == "__main__":
    unittest.main()
