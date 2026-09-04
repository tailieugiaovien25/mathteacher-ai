from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STANDARDIZER = ROOT / "src" / "document_standardization" / "lesson_plan_standardizer.py"
SCOPE = ROOT / "src" / "document_standardization" / "lesson_plan_multi_period_scope.py"


def test_background_cleanup_runs_for_table_standardization():
    text = STANDARDIZER.read_text(encoding="utf-8-sig")
    assert "self._normalize_global_text_color(" in text
    assert 'properties.remove(\n                        highlight' in text
    assert 'tc_pr.remove(cell_shading)' in text


def test_table_border_and_image_fit_are_wired():
    text = STANDARDIZER.read_text(encoding="utf-8-sig")
    assert "self._set_table_borders(table, table_profile)" in text
    assert "def _normalize_cell_borders(" in text
    assert "def _fit_cell_drawings(" in text
    assert 'changes["cell_images_scaled_to_fit"] += 1' in text
    assert 'changes["cell_border_overrides_removed"] += 1' in text


def test_a9b_r2_row_split_guard_is_preserved():
    text = STANDARDIZER.read_text(encoding="utf-8-sig")
    assert text.count('OxmlElement(\n                            "w:cantSplit"') == 1
    assert "row_index == 0" in text
    assert 'OxmlElement(\n                        "w:tblHeader"' in text


def test_multi_period_overlay_does_not_generate_planning_date():
    text = SCOPE.read_text(encoding="utf-8-sig")
    function_text = text.split("def apply_scoped_english_period_dates", 1)[1]
    assert "planning_owner_period = min(selected) if selected else None" in function_text
    assert 'label="Date of planning"' in function_text
    assert 'label="Date of teaching"' in function_text
    assert "if teaching_replaced:" in function_text
