from pathlib import Path
import ast


UI_PATH = Path(
    "src/portal_v2/ui/"
    "weekly_schedule_streamlit.py"
)


def _source():
    return UI_PATH.read_text(
        encoding="utf-8-sig"
    )


def _tree():
    return ast.parse(
        _source()
    )


def _drafting_function():
    for node in _tree().body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name
            == "_render_lesson_plan_drafting_workspace"
        ):
            return node

    raise AssertionError(
        "drafting workspace function not found"
    )


def _drafting_source():
    return ast.get_source_segment(
        _source(),
        _drafting_function(),
    )


def _drafting_strings():
    return {
        node.value
        for node in ast.walk(
            _drafting_function()
        )
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        )
    }


def _has_string(value):
    return value in _drafting_strings()


def test_drafting_workspace_function_exists():
    assert (
        _drafting_function().name
        == "_render_lesson_plan_drafting_workspace"
    )


def test_workspace_supports_current_drafting_entry():
    assert _has_string(
        "C\u00e1ch b\u1eaft \u0111\u1ea7u"
    )

    source = _drafting_source()

    assert (
        "st.radio("
        in source
    )



def test_workspace_supports_existing_plan_editing():
    assert _has_string(
        "T\u1ea3i gi\u00e1o \u00e1n "
        "c\u0169 \u0111\u1ec3 ch\u1ec9nh s\u1eeda"
    )

    assert _has_string(
        "\u0110\u01b0a gi\u00e1o \u00e1n "
        "v\u00e0o tr\u00ecnh ch\u1ec9nh s\u1eeda"
    )



def test_workspace_keeps_existing_word_upload():
    assert _has_string(
        "T\u1ea3i gi\u00e1o \u00e1n "
        "c\u0169 \u0111\u1ec3 ch\u1ec9nh s\u1eeda"
    )

    source = _drafting_source()

    assert (
        "st.file_uploader("
        in source
    )



def test_workspace_has_objectives_editor():
    strings = _drafting_strings()

    assert any(
        "I. M\u1ee4C TI\u00caU" in value
        for value in strings
    )

    source = _drafting_source()

    assert "objectives_key =" in source
    assert 'prefix + "_objectives"' in source


def test_workspace_has_materials_editor():
    strings = _drafting_strings()

    assert any(
        "II. THI\u1ebeT B\u1eca V\u00c0 H\u1eccC LI\u1ec6U"
        in value
        for value in strings
    )

    source = _drafting_source()

    assert "materials_key =" in source
    assert 'prefix + "_materials"' in source


def test_workspace_has_teaching_process_editor():
    strings = _drafting_strings()

    assert any(
        "III. TI\u1ebeN TR\u00ccNH D\u1ea0Y H\u1eccC"
        in value
        for value in strings
    )

    source = _drafting_source()

    assert "process_key =" in source
    assert 'prefix + "_process"' in source


def test_workspace_has_draft_save_action():
    assert _has_string(
        "L\u01b0u b\u1ea3n nh\u00e1p"
    )

    source = _drafting_source()

    assert 'prefix + "_save"' in source


def test_workspace_has_standardization_transition():
    assert _has_string(
        "\u27a1\ufe0f Chuy\u1ec3n sang "
        "Chu\u1ea9n h\u00f3a gi\u00e1o \u00e1n "
        "theo L\u1ecbch b\u00e1o gi\u1ea3ng"
    )



def test_workspace_has_draft_save_action():
    assert _has_string(
        "L\u01b0u b\u1ea3n nh\u00e1p"
    )

    source = _drafting_source()

    assert (
        'prefix + "_save"'
        in source
        or
        "L\u01b0u b\u1ea3n nh\u00e1p"
        in source
    )



def test_workspace_uses_scoped_identity():
    source = _drafting_source()

    assert "context.widget_prefix" in source
    assert "LessonPlanWorkspaceContext" in source

    assert (
        '"lbg_drafting_objectives"'
        not in source
    )

    assert (
        '"lbg_drafting_materials"'
        not in source
    )

    assert (
        '"lbg_drafting_process"'
        not in source
    )


def test_workspace_loads_persisted_draft():
    source = _drafting_source()

    assert "workspace_service.load(" in source

    assert (
        "persisted.objectives_text"
        in source
    )

    assert (
        "persisted.materials_text"
        in source
    )

    assert (
        "persisted.teaching_process_text"
        in source
    )


def test_existing_standardization_workspace_is_preserved():
    functions = {
        node.name
        for node in ast.walk(
            _tree()
        )
        if isinstance(
            node,
            ast.FunctionDef,
        )
    }

    assert (
        "_render_lesson_plan_standardization_workspace"
        in functions
    )


def test_existing_lesson_selector_is_preserved():
    text = _source()

    assert (
        "LessonPlanUnitSelectorService"
        in text
    )

    assert (
        "LessonPlanSelectionMode.LESSON"
        in text
    )
