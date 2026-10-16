import unittest

from shared_knowledge_library import SharedKnowledgeLibrary
from shared_knowledge_library.service import SharedKnowledgeLibraryService
from teacher_document_library_v2.models import TeacherDocument, DocumentCategory


class FakeCatalog:
    def __init__(self, document):
        self.document = document

    def get(self, document_id):
        if document_id == self.document.document_id:
            return self.document
        return None


class TeacherDocumentBridgeTests(unittest.TestCase):

    def test_teacher_document_is_registered_without_mutation(self):
        document = TeacherDocument(
            document_id="11111111-1111-1111-1111-111111111111",
            title="Toán 7 - Hình học",
            category=list(DocumentCategory)[0],
            academic_year="2026-2027",
            subject="Toán",
            grade_level="7",
            class_name=None,
            file_name="toan7.pdf",
            mime_type="application/pdf",
            size_bytes=1000,
            storage_provider="local",
            storage_file_id="file-001",
            tags=("toan7", "hinhhoc"),
        )

        catalog = FakeCatalog(document)
        library = SharedKnowledgeLibrary()
        service = SharedKnowledgeLibraryService(catalog, library)

        result = service.register_document(document.document_id)

        self.assertEqual(result.document_id, document.document_id)
        self.assertEqual(result.title, document.title)
        self.assertEqual(result.file_name, document.file_name)
        self.assertEqual(result.storage_file_id, document.storage_file_id)

        original = catalog.get(document.document_id)
        self.assertEqual(original.title, "Toán 7 - Hình học")
        self.assertEqual(original.storage_file_id, "file-001")

        self.assertIsNotNone(
            library.get(document.document_id)
        )


if __name__ == "__main__":
    unittest.main()
