from docx import Document
from docx.shared import Pt

from mathteacher_ai.document_transformation.docx_transformer import transform_docx


def _make_source(path):
    doc = Document()
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Date of planning:……\\nDate of teaching:……\\nWEEK: 11"
    table.cell(0, 1).text = "Period 28: Unit 4\\nLesson 3"
    doc.save(path)


def test_transform_removes_week_and_preserves_source(tmp_path):
    source = tmp_path / "source.docx"
    output = tmp_path / "output.docx"
    _make_source(source)

    transform_docx(source, output)
    result = Document(output)
    assert source.exists()
    assert "WEEK:" not in result.tables[0].cell(0, 0).text
    assert result.tables[0].cell(0, 1).text == "Period 28: Unit 4\\nLesson 3"


def test_date_fields_are_italic_not_bold_and_week_is_removed(tmp_path):
    source = tmp_path / "source.docx"
    output = tmp_path / "output.docx"
    _make_source(source)

    transform_docx(source, output, date_map={
        "28": {
            "planning": "06/11/2026",
            "6A1": "10/11/2026",
            "6A2": "10/11/2026",
        }
    })
    result = Document(output)
    cell = result.tables[0].cell(0, 0)
    assert "WEEK:" not in cell.text
    assert len(cell.paragraphs) == 3
    date_runs = [run for paragraph in cell.paragraphs for run in paragraph.runs]
    assert all(run.italic is True and run.bold is False for run in date_runs)
    assert all(run.font.name == "Times New Roman" and run.font.size == Pt(14) for run in date_runs)
    assert cell.paragraphs[0].text == "Date of planning: 06/11/2026"
    assert cell.paragraphs[1].text == "Date of teaching: 10/11/2026 (6A1)"
    assert cell.paragraphs[2].text == "10/11/2026 (6A2)"
