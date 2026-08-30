from pathlib import Path

SOURCE = Path("src/portal_v2/ui/weekly_schedule_streamlit.py").read_text(encoding="utf-8-sig")

def test_emitter_is_idempotent():
    assert "if getattr(current, field) == value:" in SOURCE

def test_grade_uses_exact_dynamic_key():
    block = SOURCE[SOURCE.index("def _autosave_standardization_change"):SOURCE.index("def _emit_canonical_week_change")]
    assert "st.session_state.get(state_key)" in block
    assert 'startswith("standardization_grade_filter_")' not in block
    assert 'args=("Khối lớp", grade_filter_key)' in SOURCE

def test_projection_markers():
    assert 'source_control="standardization_subject_filter_projection"' in SOURCE
    assert 'source_control="standardization_component_filter_projection"' in SOURCE
    assert "PPCT is downstream of canonical grade" in SOURCE
    assert "source_control=grade_filter_key" not in SOURCE

def test_class_and_multiclass_preserved():
    assert 'source_control="standardization_selected_timetable_row"' in SOURCE
    assert "selected_class_ids = tuple(dict.fromkeys(" in SOURCE
