from pathlib import Path
import ast


UI_PATH = Path(
    "src/portal_v2/ui/"
    "weekly_schedule_streamlit.py"
)


def _tree():
    return ast.parse(
        UI_PATH.read_text(
            encoding="utf-8-sig"
        )
    )


def _function(name):
    for node in ast.walk(_tree()):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == name
        ):
            return node

    raise AssertionError(
        f"function not found: {name}"
    )


def test_standardization_workspace_calls_drafting_workspace():
    function = _function(
        "_render_lesson_plan_standardization_workspace"
    )

    calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
    ]

    assert any(
        isinstance(call.func, ast.Name)
        and call.func.id
        == "_render_lesson_plan_drafting_workspace"
        for call in calls
    )


def test_selected_lesson_is_passed_to_drafting_workspace():
    function = _function(
        "_render_lesson_plan_standardization_workspace"
    )

    matching_calls = []

    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue

        if not (
            isinstance(node.func, ast.Name)
            and node.func.id
            == "_render_lesson_plan_drafting_workspace"
        ):
            continue

        matching_calls.append(node)

    assert len(matching_calls) == 1

    call = matching_calls[0]

    keywords = {
        item.arg: item.value
        for item in call.keywords
        if item.arg is not None
    }

    assert "selected_lesson" in keywords

    value = keywords["selected_lesson"]

    assert isinstance(value, ast.Name)
    assert value.id == "selected_lesson"


def test_drafting_workspace_function_is_preserved():
    functions = {
        node.name
        for node in ast.walk(_tree())
        if isinstance(node, ast.FunctionDef)
    }

    assert (
        "_render_lesson_plan_drafting_workspace"
        in functions
    )


def test_existing_standardization_processing_is_preserved():
    source = UI_PATH.read_text(
        encoding="utf-8-sig"
    )

    assert "_process_lesson_plan_upload(" in source
    assert "render_lesson_plan_preview(" in source
    assert "render_lesson_plan_teacher_review(" in source
