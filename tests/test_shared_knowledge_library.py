import unittest

from shared_knowledge_library import (
    KnowledgeDocument,
    KnowledgeTarget,
    SharedKnowledgeLibrary,
)


class SharedKnowledgeLibraryTests(unittest.TestCase):

    def make_document(self):
        return KnowledgeDocument(
            document_id="doc-001",
            title="Toán 7 - Hình học",
            file_name="toan7-hinhhoc.pdf",
            mime_type="application/pdf",
            storage_provider="teacher_document_library",
            storage_file_id="storage-001",
            source_version="1",
            tags=("toan7", "hinhhoc"),
            targets=(
                KnowledgeTarget.LOCAL,
                KnowledgeTarget.NOTEBOOKLM,
            ),
        )

    def test_register_and_get(self):
        library = SharedKnowledgeLibrary()
        document = self.make_document()

        library.register(document)

        self.assertEqual(library.get("doc-001"), document)

    def test_local_target(self):
        library = SharedKnowledgeLibrary()
        library.register(self.make_document())

        documents = library.for_target(KnowledgeTarget.LOCAL)

        self.assertEqual(len(documents), 1)

    def test_notebooklm_is_optional_target(self):
        library = SharedKnowledgeLibrary()
        library.register(self.make_document())

        documents = library.for_target(KnowledgeTarget.NOTEBOOKLM)

        self.assertEqual(len(documents), 1)

    def test_remove(self):
        library = SharedKnowledgeLibrary()
        library.register(self.make_document())

        self.assertTrue(library.remove("doc-001"))
        self.assertIsNone(library.get("doc-001"))

    def test_invalid_document_is_rejected(self):
        with self.assertRaises(ValueError):
            KnowledgeDocument(
                document_id="",
                title="Test",
                file_name="test.pdf",
                mime_type="application/pdf",
                storage_provider="local",
                storage_file_id="storage-1",
            )


if __name__ == "__main__":
    unittest.main()
