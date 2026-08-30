from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "src/portal_v2/ui/weekly_schedule_streamlit.py"

def _text():
    return UI.read_text(encoding="utf-8-sig")

def test_v50b_marker_exists():
    assert "STANDARDIZATION_GRADE_PPCT_CONTEXT_V50B" in _text()

def test_historical_all_grades_reset_contract_is_preserved():
    text = _text()
    assert "st.session_state[grade_filter_key] = None" in text

def test_grade_state_is_week_subject_component_scoped():
    text = _text()
    pos = text.index("grade_filter_key = (")
    block = text[pos:pos + 450]
    assert "view.week_number" in block
    assert "selected_subject_ref" in block
    assert "selected_component_ref" in block

def test_single_available_grade_is_auto_selected():
    text = _text()
    assert "len(available_grades) == 1" in text
    assert "current_grade_filter = available_grades[0]" in text

def test_mode_and_ppct_keys_are_grade_scoped():
    text = _text()
    assert "grade_context_token = (" in text
    mode = text[text.index("mode_widget_key = ("):][:500]
    unit = text[text.index("unit_widget_key = ("):][:600]
    assert '"_grade_"' in mode
    assert "grade_context_token" in mode
    assert '"_grade_"' in unit
    assert "grade_context_token" in unit

def test_ppct_build_uses_grade_filtered_week_rows():
    text = _text()
    grade = text.index("if selected_grade is not None:")
    build = text.index("selector.build_units(", grade)
    assert grade < build
    block = text[build:build + 400]
    assert "rows=filtered_schedule_rows" in block
    assert "WEEK_SCOPED_PPCT_OPTIONS_V1" in block

def test_transfer_matching_and_indexing_share_filtered_rows():
    text = _text()
    start = text.index("transfer_key, incoming_transfer")
    match = text.index("_match_transfer_schedule_row(", start)
    assert "filtered_schedule_rows" in text[match:match + 220]
    assert "matched_row = filtered_schedule_rows[" in text
