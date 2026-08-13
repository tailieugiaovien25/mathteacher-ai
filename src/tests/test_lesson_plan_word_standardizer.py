from pathlib import Path

import pytest
from docx import Document

from document_standardization import LessonPlanWordStandardizer


PROFILE = {
    "profile_name": "test", "page": {"margin_left_cm": 3, "margin_right_cm": 2, "margin_top_cm": 2, "margin_bottom_cm": 2},
    "body": {"font": "Times New Roman", "size_pt": 13, "line_spacing": 1.15},
    "title": {"size_pt": 14}, "table": {"size_pt": 12},
    "equations": {"mode": "safe", "text_font": "Times New Roman"},
}


def make_docx(path: Path):
    document = Document()
    document.add_paragraph("BÀI 1: BÀI HỌC MẪU")
    document.add_paragraph("I. MỤC TIÊU")
    document.add_paragraph("Nội dung không được thay đổi.")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text, table.cell(0, 1).text = "HOẠT ĐỘNG", "SẢN PHẨM"
    table.cell(1, 0).text, table.cell(1, 1).text = "GV giao nhiệm vụ", "Câu trả lời"
    document.save(path)


def test_standardizer_preserves_source_and_content(tmp_path):
    source, output, report = tmp_path / "source.docx", tmp_path / "out.docx", tmp_path / "report.json"
    make_docx(source)
    source_bytes = source.read_bytes()
    result = LessonPlanWordStandardizer(PROFILE).standardize(source, output, report)
    assert source.read_bytes() == source_bytes
    assert output.exists() and report.exists() and result["source_preserved"]
    document = Document(output)
    assert "Nội dung không được thay đổi." in "\n".join(p.text for p in document.paragraphs)
    assert len(document.tables) == 1
    assert document.paragraphs[0].runs[0].font.name == "Times New Roman"


def test_standardizer_refuses_to_overwrite_source(tmp_path):
    source = tmp_path / "source.docx"; make_docx(source)
    with pytest.raises(ValueError, match="ghi đè"):
        LessonPlanWordStandardizer(PROFILE).standardize(source, source, tmp_path / "report.json")
