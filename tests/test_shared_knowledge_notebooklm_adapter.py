import unittest

from shared_knowledge_library.library import KnowledgeDocument
from shared_knowledge_library.notebooklm_adapter import SharedKnowledgeNotebookLMAdapter


class FakeNotebookLMClient:
    def __init__(self):
        self.calls = []

    def upload_file(self, notebook_id, file_path, display_name, content_type):
        self.calls.append({
            "notebook_id": notebook_id,
            "file_path": file_path,
            "display_name": display_name,
            "content_type": content_type,
        })
        return "fake-upload-001"


class NotebookLMAdapterContractTests(unittest.TestCase):

    def test_shared_knowledge_maps_to_notebooklm_upload_contract(self):
        client = FakeNotebookLMClient()
        adapter = SharedKnowledgeNotebookLMAdapter(client)

        document = KnowledgeDocument(
            document_id="550e8400-e29b-41d4-a716-446655440000",
            title="Toán 6",
            file_name="toan6.docx",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            storage_provider="local",
            storage_file_id="storage-test-001",
        )

        result = adapter.sync(document)

        self.assertEqual(result, "fake-upload-001")
        self.assertEqual(len(client.calls), 1)

        call = client.calls[0]
        self.assertEqual(call["notebook_id"], "dry-run-notebook")
        self.assertEqual(call["file_path"], "toan6.docx")
        self.assertEqual(call["display_name"], "Toán 6")
        self.assertEqual(call["content_type"], document.mime_type)


if __name__ == "__main__":
    unittest.main()
