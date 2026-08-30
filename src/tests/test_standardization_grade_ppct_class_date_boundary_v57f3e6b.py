from pathlib import Path

P = Path("src/portal_v2/ui/weekly_schedule_streamlit.py")

def _source():
    return P.read_text(encoding="utf-8-sig")

def test_f3e6b_has_grade_filtered_hard_boundary():
    text = _source()
    assert "_v58_resolved_lbg_lesson_context" in text
    assert "Projection envelope only; canonical scalar SystemContext remains authority" in text

def test_f3e6b_blocks_wider_schedule_rows():
    text = _source()
    assert "Multi-class consumers must read this envelope" in text
    assert "instead of re-expanding" in text

def test_f3e6b_preserves_existing_same_lesson_expansion():
    text = _source()
    assert "_rows_for_same_timetable_lesson(" in text

def test_grade_filter_precedes_selected_timetable_rows():
    text = _source()
    grade_filter = text.index("if selected_grade is not None:", text.index("STANDARDIZATION_GRADE_PPCT_CONTEXT_V50B"))
    projection = text.index('st.session_state["_v58_resolved_lbg_lesson_context"]', grade_filter)
    assert grade_filter < projection

def test_class_and_date_derive_from_selected_timetable_rows():
    text = _source()
    anchor = text.index("resolved_lbg_lesson_context = {")
    tail = text[anchor:anchor + 3000]
    assert '"class_ids"' in tail
    assert '"teaching_dates_by_class"' in tail
    assert '"representative_teaching_date"' in tail
