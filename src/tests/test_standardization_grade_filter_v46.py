from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "src/portal_v2/ui/weekly_schedule_streamlit.py"


def _text() -> str:
    return UI.read_text(encoding="utf-8-sig")


def test_grade_filter_is_rendered_in_fifth_selector_column():
    text = _text()
    assert 'selector_columns[4].selectbox(' in text
    assert '"Khối lớp"' in text


def test_grade_filter_has_safe_all_grades_default():
    text = _text()
    assert 'grade_filter_options = (None,) + available_grades' in text
    assert '"Tất cả khối"' in text


def test_grade_filter_supports_thcs_grades_6_to_9():
    text = _text()
    assert 'for grade in range(6, 10)' in text
    assert 'else f"Lớp {grade}"' in text


def test_grade_filter_runs_before_unit_building():
    text = _text()
    a = text.index("STANDARDIZATION_GRADE_FILTER_V46")
    b = text.index("selector.build_units(", a)
    c = text.index("if selected_grade is not None:", a)
    assert a < c < b


def test_all_grades_keeps_previous_behavior():
    text = _text()
    assert "if selected_grade is not None:" in text
    assert 'st.session_state[grade_filter_key] = None' in text
