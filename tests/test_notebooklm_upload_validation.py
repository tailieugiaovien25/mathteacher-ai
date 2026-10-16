from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from notebooklm_bridge.adapters.notebooklm import (
    NotebookLMAdapter,
    NotebookLMAdapterConfig,
)


class FakeUploadClient:
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
        return f"fake-source/{display_name}"


class TestNotebookLMUploadValidation(unittest.TestCase):

    def setUp(self) -> None:
        self.adapter = NotebookLMAdapter(
            config=NotebookLMAdapterConfig(enabled=True),
            client=FakeUploadClient(),
        )

    def test_supported_document_types_contract(self) -> None:
        supported = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".docx": (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            ".pptx": (
                "application/vnd.openxmlformats-officedocument."
                "presentationml.presentation"
            ),
            ".xlsx": (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        }

        for suffix, content_type in supported.items():
            with self.subTest(suffix=suffix):
                with tempfile.NamedTemporaryFile(
                    suffix=suffix,
                    delete=False,
                ) as handle:
                    path = Path(handle.name)

                try:
                    result = self.adapter.upload_file(
                        notebook_id="notebook-001",
                        file_path=path,
                        display_name=f"source{suffix}",
                        content_type=content_type,
                    )
                    self.assertEqual(
                        result,
                        f"fake-source/source{suffix}",
                    )
                finally:
                    path.unlink(missing_ok=True)

    def test_empty_notebook_id_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "notebook_id must not be empty",
        ):
            self.adapter.upload_file(
                notebook_id="",
                file_path="test.pdf",
                display_name="test.pdf",
                content_type="application/pdf",
            )

    def test_empty_file_path_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "file_path must not be empty",
        ):
            self.adapter.upload_file(
                notebook_id="notebook-001",
                file_path="",
                display_name="test.pdf",
                content_type="application/pdf",
            )

    def test_empty_display_name_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "display_name must not be empty",
        ):
            self.adapter.upload_file(
                notebook_id="notebook-001",
                file_path="test.pdf",
                display_name="",
                content_type="application/pdf",
            )

    def test_empty_content_type_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "content_type must not be empty",
        ):
            self.adapter.upload_file(
                notebook_id="notebook-001",
                file_path="test.pdf",
                display_name="test.pdf",
                content_type="",
            )


if __name__ == "__main__":
    unittest.main()
