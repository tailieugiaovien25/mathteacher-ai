import io
import json
import unittest
import uuid
import zipfile
from datetime import datetime, timezone

from teacher_document_library_v2.models import DocumentCategory, TeacherDocument
from notebooklm_bridge.source_pack import build_notebooklm_source_pack


class TestNotebookLMSourcePack(unittest.TestCase):
    def _document(self, *, title: str, file_name: str) -> TeacherDocument:
        return TeacherDocument(
            document_id=str(uuid.uuid4()),
            title=title,
            category=DocumentCategory.LESSON_PLAN,
            academic_year="2026-2027",
            subject="Toán",
            grade_level="7",
            class_name="7A1",
            file_name=file_name,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes=0,
            storage_provider="test",
            storage_file_id=str(uuid.uuid4()),
            web_view_link="https://example.test/document",
            description="Tài liệu kiểm thử NotebookLM.",
            tags=("Toán", "lớp 7"),
        )

    def test_build_source_pack_with_selected_documents(self):
        doc1 = self._document(
            title="Giáo án Toán 7",
            file_name="giao_an_toan_7.docx",
        )
        doc2 = self._document(
            title="Giáo án hình học",
            file_name="giao_an_hinh_hoc.docx",
        )

        files = {
            doc1.document_id: b"noi dung giao an 1",
            doc2.document_id: b"noi dung giao an 2",
        }

        def download_document(document):
            return files[document.document_id]

        now = datetime(2026, 10, 11, 8, 0, tzinfo=timezone.utc)

        pack = build_notebooklm_source_pack(
            [doc1, doc2],
            download_document,
            now=now,
        )

        self.assertTrue(pack.filename.endswith(".zip"))
        self.assertEqual(len(pack.included_sources), 2)
        self.assertEqual(pack.failed_sources, ())

        with zipfile.ZipFile(io.BytesIO(pack.content), "r") as archive:
            names = archive.namelist()

            self.assertIn("README_NOTEBOOKLM_VI.md", names)
            self.assertIn("SOURCE_INDEX.md", names)
            self.assertIn("source_manifest.json", names)
            self.assertIn("source_manifest.csv", names)
            self.assertIn("NOTEBOOKLM_PROMPTS_VI.md", names)

            source_files = [
                name for name in names
                if name.startswith("sources/")
            ]

            self.assertEqual(len(source_files), 2)

            manifest = json.loads(
                archive.read("source_manifest.json").decode("utf-8")
            )

            self.assertEqual(len(manifest["sources"]), 2)

    def test_download_failure_is_reported_without_losing_successful_sources(self):
        good = self._document(
            title="Tài liệu tốt",
            file_name="tai_lieu_tot.docx",
        )
        bad = self._document(
            title="Tài liệu lỗi",
            file_name="tai_lieu_loi.docx",
        )

        def download_document(document):
            if document.document_id == bad.document_id:
                raise RuntimeError("download failed")
            return b"noi dung hop le"

        pack = build_notebooklm_source_pack(
            [good, bad],
            download_document,
            now=datetime(2026, 10, 11, 8, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(len(pack.included_sources), 1)
        self.assertEqual(len(pack.failed_sources), 1)

        self.assertEqual(
            pack.failed_sources[0]["document_id"],
            bad.document_id,
        )

        with zipfile.ZipFile(io.BytesIO(pack.content), "r") as archive:
            source_files = [
                name for name in archive.namelist()
                if name.startswith("sources/")
            ]

            self.assertEqual(len(source_files), 1)

    def test_duplicate_document_selection_is_rejected(self):
        document = self._document(
            title="Tài liệu trùng",
            file_name="tai_lieu_trung.docx",
        )

        with self.assertRaises(Exception):
            build_notebooklm_source_pack(
                [document, document],
                lambda _: b"content",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)

