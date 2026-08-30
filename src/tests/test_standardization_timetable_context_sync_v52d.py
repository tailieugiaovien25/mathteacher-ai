from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "src/portal_v2/ui/weekly_schedule_streamlit.py"

def source():
    return UI.read_text(encoding="utf-8-sig")

def test_v52d_marker():
    assert "STANDARDIZATION_TIMETABLE_CONTEXT_SYNC_V52D" in source()

def test_week_rows_are_canonical_source():
    text = source()
    assert "V52D canonical weekly timetable source" in text
    assert "schedule_rows = tuple(" in text
    assert "view.rows" in text

def test_subject_state_is_validated_before_subject_widget():
    text = source()
    validation = text.index("_standardization_keep_valid_option(\n        \"standardization_subject_filter\"")
    widget = text.index('selected_subject_ref = st.selectbox(')
    assert validation < widget

def test_component_state_is_validated_before_component_widget():
    text = source()
    validation = text.index("_standardization_keep_valid_option(\n        \"standardization_component_filter\"")
    widget = text.index('selected_component_ref = st.selectbox(')
    assert validation < widget

def test_ppct_state_is_validated_without_shadowing_v51_contract():
    text = source()
    assert "_standardization_keep_valid_option(\n        unit_widget_key," in text
    first_literal_key = text.index("key=unit_widget_key,")
    block = text[first_literal_key:first_literal_key + 700]
    assert "on_change=_standardization_ppct_reverse_sync" in block

def test_existing_week_grade_reverse_contracts_remain():
    text = source()
    assert "WEEK_SCOPED_PPCT_OPTIONS_V1" in text
    assert "rows=filtered_schedule_rows" in text
    assert "STANDARDIZATION_GRADE_PPCT_CONTEXT_V50B" in text
    assert "STANDARDIZATION_PPCT_REVERSE_SYNC_V51" in text
