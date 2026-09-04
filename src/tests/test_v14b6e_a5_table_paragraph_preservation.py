from pathlib import Path

TARGET = (
    Path(__file__).resolve().parents[1]
    / "document_standardization"
    / "lesson_plan_standardizer.py"
)

def test_table_cell_alignment_and_before_after_spacing_are_preserved():
    text = TARGET.read_text(encoding="utf-8")
    assert 'fmt.line_spacing = body["line_spacing"]' in text
    assert "if not in_table:" in text
    assert "fmt.space_before = Pt(0)" in text
    assert "fmt.space_after = Pt(0)" in text

def test_table_width_logic_is_unchanged():
    text = TARGET.read_text(encoding="utf-8")
    assert "table.autofit = False" in text
    assert "original_total > usable_dxa" in text
    assert "and original_total" in text
    assert '"tables_content_autofit"' in text

def test_line_spacing_compliance_scope_is_unchanged():
    text = TARGET.read_text(encoding="utf-8")
    assert "for paragraph in self._all_paragraphs(document):" in text
    assert "if paragraph.text and paragraph.paragraph_format.line_spacing != expected_line:" in text
    assert 'add("LINE_SPACING", not bad_lines, expected_line, bad_lines[:20])' in text
