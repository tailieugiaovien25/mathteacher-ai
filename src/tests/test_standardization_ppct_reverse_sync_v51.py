from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
UI=ROOT/"src/portal_v2/ui/weekly_schedule_streamlit.py"
def _text(): return UI.read_text(encoding="utf-8-sig")
def test_v51_marker():
    assert "STANDARDIZATION_PPCT_REVERSE_SYNC_V51" in _text()
def test_callback():
    t=_text()
    p=t.index("key=unit_widget_key,")
    b=t[p:p+700]
    assert "on_change=_standardization_ppct_reverse_sync" in b
    assert '"lesson_units": lesson_units' in b
    assert '"filtered_schedule_rows": filtered_schedule_rows' in b
def test_reverse_grade():
    t = _text()
    a = t.index("def _standardization_ppct_reverse_sync(")
    b = t.index("def _render_lesson_plan_standardization_workspace(", a)
    s = t[a:b]
    assert "selected_unit.representative_index" in s
    assert "PPCT is downstream of canonical grade" in s
    assert "get_canonical_context(" in s
    assert "st.session_state[grade_filter_key] = selected_grade" not in s
def test_context_fields():
    t=_text()
    a=t.index("def _standardization_ppct_reverse_sync(")
    b=t.index("def _render_lesson_plan_standardization_workspace(",a)
    s=t[a:b]
    for f in ('"subject_ref"','"component_ref"','"class_id"','"curriculum_period"','"lesson_title"','"grade"'):
        assert f in s
def test_week_scope_preserved():
    t=_text()
    p=t.index("selector.build_units(")
    assert "rows=filtered_schedule_rows" in t[p:p+450]
def test_v50b_preserved():
    t=_text()
    assert "STANDARDIZATION_GRADE_PPCT_CONTEXT_V50B" in t
    assert "st.session_state[grade_filter_key] = None" in t
