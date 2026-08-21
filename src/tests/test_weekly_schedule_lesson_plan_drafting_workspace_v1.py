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


def _string_literals():
    return {
        node.value
        for node in ast.walk(_tree())
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        )
    }


def _has_string(value):
    return value in _string_literals()


def test_drafting_workspace_function_exists():
    functions = {
        node.name
        for node in ast.walk(_tree())
        if isinstance(node, ast.FunctionDef)
    }

    assert (
        "_render_lesson_plan_drafting_workspace"
        in functions
    )


def test_workspace_supports_new_draft_mode():
    assert _has_string(
        "So\u1ea1n m\u1edbi"
    )


def test_workspace_supports_existing_plan_mode():
    assert _has_string(
        "D\u00f9ng gi\u00e1o \u00e1n "
        "\u0111\u00e3 c\u00f3"
    )


def test_workspace_keeps_word_upload_mode():
    assert _has_string(
        "T\u1ea3i Word l\u00ean"
    )


def test_workspace_has_objectives_editor():
    strings = _string_literals()

    assert any(
        "I. M\u1ee4C TI\u00caU" in value
        for value in strings
    )

    assert _has_string(
        "lbg_drafting_objectives"
    )


def test_workspace_has_materials_editor():
    strings = _string_literals()

    assert any(
        (
            "II. THI\u1ebeT B\u1eca "
            "V\u00c0 H\u1eccC LI\u1ec6U"
        )
        in value
        for value in strings
    )

    assert _has_string(
        "lbg_drafting_materials"
    )


def test_workspace_has_teaching_process_editor():
    strings = _string_literals()

    assert any(
        (
            "III. TI\u1ebeN TR\u00ccNH "
            "D\u1ea0Y H\u1eccC"
        )
        in value
        for value in strings
    )

    assert _has_string(
        "lbg_drafting_process"
    )


def test_workspace_has_draft_save_action():
    assert _has_string(
        "L\u01b0u b\u1ea3n nh\u00e1p"
    )

    assert _has_string(
        "lbg_drafting_save"
    )


def test_workspace_has_preview_action():
    assert _has_string(
        "Xem tr\u01b0\u1edbc"
    )

    assert _has_string(
        "lbg_drafting_preview"
    )


def test_workspace_has_word_export_action():
    assert _has_string(
        "Xu\u1ea5t Word"
    )

    assert _has_string(
        "lbg_drafting_export_word"
    )


def test_existing_standardization_workspace_is_preserved():
    functions = {
        node.name
        for node in ast.walk(_tree())
        if isinstance(node, ast.FunctionDef)
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
