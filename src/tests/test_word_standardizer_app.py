from pathlib import Path

import pytest
from docx import Document

from scripts.word_standardizer.app import standardize_uploaded_docx


def test_web_app_standardizes_uploaded_docx_and_returns_downloads(tmp_path):
    source = tmp_path / "giao-an.docx"
    document = Document()
    document.add_paragraph("BÀI 1: BÀI HỌC MẪU")
    document.save(source)

    output_name, output_bytes, report_name, report_bytes, report = standardize_uploaded_docx(
        source.read_bytes(), "giao-an.docx"
    )

    assert output_name == "giao-an.standardized.docx"
    assert output_bytes.startswith(b"PK")
    assert report_name == "giao-an.standardization-report.json"
    assert b'"source_preserved": true' in report_bytes
    assert report["source_preserved"] is True


def test_web_app_rejects_non_docx_upload():
    with pytest.raises(ValueError, match=".docx"):
        standardize_uploaded_docx(b"not-a-document", "giao-an.doc")
