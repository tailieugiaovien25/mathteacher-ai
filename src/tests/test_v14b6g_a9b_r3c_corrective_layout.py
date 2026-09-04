from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STANDARDIZER = ROOT / "src" / "document_standardization" / "lesson_plan_standardizer.py"
SCOPE = ROOT / "src" / "document_standardization" / "lesson_plan_multi_period_scope.py"


def test_background_cleanup_is_canonical_and_unconditional():
    text = STANDARDIZER.read_text(encoding="utf-8-sig")
    call = "self._normalize_global_text_color(\n            document,\n            changes,\n        )"
    assert call in text
    assert "if options.normalize_font or options.normalize_tables:" not in text
    assert "tc_pr.remove(cell_shading)" in text


def test_drawing_cleanup_handles_crop_anchor_and_safe_width():
    text = STANDARDIZER.read_text(encoding="utf-8-sig")
    assert '(width_dxa - 720) * 635' in text
    assert 'local-name()="srcRect"' in text
    assert 'offset.text = "0"' in text
    assert "def _fit_cell_drawings(" in text


def test_only_first_selected_period_keeps_planning_field():
    text = SCOPE.read_text(encoding="utf-8-sig")
    assert "planning_owner_period = min(selected) if selected else None" in text
    assert "period != planning_owner_period" in text
    assert "def _remove_english_planning_field(" in text
    function_text = text.split("def apply_scoped_english_period_dates", 1)[1]
    assert 'label="Date of planning"' in function_text
    assert 'label="Date of teaching"' in function_text


def test_a9b_r2_row_split_guard_remains_single_header_only():
    text = STANDARDIZER.read_text(encoding="utf-8-sig")
    assert text.count('OxmlElement(\n                            "w:cantSplit"') == 1
    assert "row_index == 0" in text
    assert 'OxmlElement(\n                        "w:tblHeader"' in text
