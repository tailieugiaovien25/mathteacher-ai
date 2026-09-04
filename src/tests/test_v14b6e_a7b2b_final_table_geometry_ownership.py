from pathlib import Path

TARGET = Path("src/portal_v2/ui/weekly_schedule_streamlit.py")


def _reflow_block() -> str:
    text = TARGET.read_text(encoding="utf-8")
    start = text.index("def _mt_reflow_all_lesson_tables(document):")
    end = text.index("\ndef ", start + 4)
    return text[start:end]


def test_final_reflow_does_not_override_table_autofit_geometry():
    block = _reflow_block()
    assert "table.autofit = True" not in block
    assert "table.autofit = False" not in block


def test_final_reflow_preserves_cleanup_contracts():
    block = _reflow_block()
    assert 'tr_pr.xpath("./w:trHeight")' in block
    assert "WD_CELL_VERTICAL_ALIGNMENT.TOP" in block
    assert "_mt_remove_redundant_empty_cell_paragraphs(cell)" in block


def test_standardizer_remains_geometry_owner():
    text = Path(
        "src/document_standardization/lesson_plan_standardizer.py"
    ).read_text(encoding="utf-8")
    assert "table.autofit = False" in text
    # A8B keeps LessonPlanWordStandardizer as the geometry owner,
    # but replaces the retired single proportional-scaling branch
    # with a hybrid policy: fixed semantic balancing for eligible
    # two-column tables and content autofit for wide/complex tables.
    assert "original_total > usable_dxa" in text
    assert "self._apply_fixed_widths(" in text
    assert "self._apply_content_autofit(" in text
    assert "table.autofit = False" in text
    assert "table.autofit = True" in text
    # The retired single proportional-scaling counter is no longer
    # part of the ownership contract. A8B uses explicit counters for
    # its two geometry strategies instead.
    assert "tables_content_autofit" in text
    assert "two_column_tables_balanced" in text
