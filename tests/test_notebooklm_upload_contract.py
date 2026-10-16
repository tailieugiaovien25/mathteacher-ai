from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from notebooklm_bridge.adapters.notebooklm import (
    NotebookLMAdapter,
    NotebookLMAdapterConfig,
)


class FakeUploadClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, str]] = []

    def sync_source(self, *, notebook_id: str, document_id: str):
        return None

    def upload_file(
        self,
        *,
        notebook_id: str,
        file_path: str | Path,
        display_name: str,
        content_type: str,
    ) -> str:
        self.calls.append(
            (
                notebook_id,
                str(file_path),
                display_name,
                content_type,
            )
        )
        return "fake-uploaded-source-001"


class TestNotebookLMUploadContract(unittest.TestCase):

    def test_adapter_delegates_upload_file(self) -> None:
        client = FakeUploadClient()

        adapter = NotebookLMAdapter(
            config=NotebookLMAdapterConfig(enabled=True),
            client=client,
        )

        with tempfile.NamedTemporaryFile(
            suffix=".docx",
            delete=False,
        ) as handle:
            path = Path(handle.name)

        try:
            result = adapter.upload_file(
                notebook_id="notebook-001",
                file_path=path,
                display_name="Bai_toan.docx",
                content_type=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
            )

            self.assertEqual(
                result,
                "fake-uploaded-source-001",
            )

            self.assertEqual(
                client.calls,
                [
                    (
                        "notebook-001",
                        str(path),
                        "Bai_toan.docx",
                        (
                            "application/vnd.openxmlformats-officedocument."
                            "wordprocessingml.document"
                        ),
                    )
                ],
            )
        finally:
            path.unlink(missing_ok=True)

    def test_disabled_adapter_rejects_upload(self) -> None:
        adapter = NotebookLMAdapter(
            config=NotebookLMAdapterConfig(enabled=False),
            client=FakeUploadClient(),
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "NotebookLM integration is disabled",
        ):
            adapter.upload_file(
                notebook_id="notebook-001",
                file_path="test.docx",
                display_name="test.docx",
                content_type=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
            )


if __name__ == "__main__":
    unittest.main()
