from pathlib import Path
SOURCE = Path("src/portal_v2/ui/weekly_schedule_streamlit.py").read_text(encoding="utf-8-sig")

def test_emitter():
    assert "def _emit_standardization_canonical_context_change(" in SOURCE

def test_fields():
    for marker in ('field="subject_ref"', 'field="component_ref"', 'field="grade"', 'field="class_id"'):
        assert marker in SOURCE

def test_class_derived():
    marker = 'source_control="standardization_selected_timetable_row"'
    assert SOURCE.index("selected_row = (") < SOURCE.index(marker)

def test_multiclass_preserved():
    assert "selected_class_ids = tuple(dict.fromkeys(" in SOURCE
