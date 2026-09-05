from pathlib import Path


UI_FILE = Path(
    "src/portal_v2/ui/teacher_timetable_streamlit.py"
)


def _source():
    return UI_FILE.read_text(encoding="utf-8")


def test_math_subject_level_scope_contract_present():
    text = _source()

    assert (
        "V14B6K_MATH_SUBJECT_LEVEL_TIMETABLE_SCOPE"
        in text
    )
    assert (
        'str(subject.code or "").strip().upper()'
        in text
    )
    assert '== "MATH"' in text
    assert "component_id=None" in text
    assert "component_name=None" in text


def test_math_subject_level_scope_precedes_component_scopes():
    text = _source()

    marker = text.index(
        "V14B6K_MATH_SUBJECT_LEVEL_TIMETABLE_SCOPE"
    )

    component_branch = text.index(
        "            if components:",
        marker,
    )

    assert marker < component_branch


def test_existing_math_component_scopes_are_preserved():
    text = _source()

    assert "component.component_id" in text
    assert "component.name" in text


def test_existing_incomplete_assignment_guard_is_preserved():
    text = _source()

    assert "and not selected_assignment_id" in text
    assert "incomplete_positions.append(" in text
