from docx import Document
from docx.shared import Pt
from mathteacher_ai.document_transformation.docx_transformer import transform_docx


def test_transform_preserves_source_text_and_media(tmp_path):
    source = tmp_path / "source.docx"
    output = tmp_path / "output.docx"
    doc = Document()
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Date of planning:……\nDate of teaching:……\nWEEK: 11"
    table.cell(0, 1).text = "Period 28: Unit 4\nLesson 3"
    doc.save(source)

    transform_docx(source, output)
    result = Document(output)
    assert result.tables[0].cell(0, 1).text == "Period 28: Unit 4\nLesson 3"
    assert source.exists()


def test_date_fields_are_italic_not_bold(tmp_path):
    source = tmp_path / "source.docx"
    output = tmp_path / "output.docx"
    doc = Document()
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Date of planning:……\nDate of teaching:……\nWEEK: 11"
    table.cell(0, 1).text = "Period 28: Unit 4\nLesson 3"
    doc.save(source)

    transform_docx(source, output, date_map={
        "28": {"planning": "06/11/2026", "6A1": "10/11/2026", "6A2": "10/11/2026"}
    })
    result = Document(output)
    date_runs = [run for para in result.tables[0].cell(0, 0).paragraphs[:3] for run in para.runs]
    assert all(run.italic is True and run.bold is False for run in date_runs)
    assert all(run.font.name == "Times New Roman" and run.font.size == Pt(14) for run in date_runs)
    assert result.tables[0].cell(0, 0).paragraphs[3].text == "WEEK: 11"
