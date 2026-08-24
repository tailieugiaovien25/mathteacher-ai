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
    for node in _tree().body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == name
        ):
            return node

    raise AssertionError(
        f"function not found: {name}"
    )


def _all_parameters(function):
    return {
        argument.arg
        for argument in (
            list(function.args.args)
            + list(function.args.kwonlyargs)
        )
    }


def _calls(function, name):
    result = []

    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue

        if (
            isinstance(node.func, ast.Name)
            and node.func.id == name
        ):
            result.append(node)

    return result


def _keywords(call):
    return {
        keyword.arg: keyword.value
        for keyword in call.keywords
        if keyword.arg is not None
    }


def test_lbg_table_accepts_teacher_user_id():
    function = _function(
        "_render_lbg_table"
    )

    assert (
        "teacher_user_id"
        in _all_parameters(function)
    )


def test_render_workspace_passes_user_id_to_lbg_table():
    function = _function(
        "render_weekly_schedule_workspace"
    )

    calls = _calls(
        function,
        "_render_lbg_table",
    )

    assert len(calls) == 1

    keywords = _keywords(
        calls[0]
    )

    assert (
        "teacher_user_id"
        in keywords
    )

    value = keywords[
        "teacher_user_id"
    ]

    assert isinstance(
        value,
        ast.Call,
    )


def test_lbg_table_passes_identity_to_standardization_workspace():
    function = _function(
        "_render_lbg_table"
    )

    calls = _calls(
        function,
        "_render_lesson_plan_standardization_workspace",
    )

    assert len(calls) == 1

    keywords = _keywords(
        calls[0]
    )

    assert (
        "teacher_user_id"
        in keywords
    )

    value = keywords[
        "teacher_user_id"
    ]

    assert isinstance(
        value,
        ast.Name,
    )

    assert (
        value.id
        == "teacher_user_id"
    )
