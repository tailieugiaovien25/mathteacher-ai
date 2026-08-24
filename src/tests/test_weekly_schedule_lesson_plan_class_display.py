import ast
from pathlib import Path


SOURCE = Path(
    "src/portal_v2/ui/"
    "weekly_schedule_streamlit.py"
)


def _source():
    return SOURCE.read_text(
        encoding="utf-8-sig"
    )


def _tree():
    return ast.parse(
        _source()
    )


def _function(name):
    for node in _tree().body:
        if (
            isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and node.name == name
        ):
            return node

    raise AssertionError(
        f"Function not found: {name}"
    )


def test_drafting_workspace_accepts_client():
    function = _function(
        "_render_lesson_plan_drafting_workspace"
    )

    names = [
        argument.arg
        for argument
        in function.args.args
    ]

    assert "client" in names


def test_drafting_workspace_uses_class_catalog():
    function = _function(
        "_render_lesson_plan_drafting_workspace"
    )

    segment = ast.get_source_segment(
        _source(),
        function,
    )

    assert (
        "SupabaseClassCatalogRepository"
        in segment
    )

    assert ".get(" in segment
    assert "class_id=class_id" in segment
    assert "class_item.class_name" in segment


def test_drafting_call_passes_client():
    source = _source()
    tree = ast.parse(source)

    calls = [
        node
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.Call)
            and isinstance(
                node.func,
                ast.Name,
            )
            and node.func.id
            == "_render_lesson_plan_drafting_workspace"
        )
    ]

    assert calls

    runtime_calls = [
        call
        for call in calls
        if any(
            keyword.arg == "client"
            for keyword
            in call.keywords
        )
    ]

    assert runtime_calls


def test_document_metadata_separates_grade_and_class():
    source = _source()
    tree = ast.parse(source)

    metadata_call = next(
        node
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.Call)
            and (
                (
                    isinstance(node.func, ast.Name)
                    and node.func.id
                    == "DocumentUploadMetadata"
                )
                or
                (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr
                    == "DocumentUploadMetadata"
                )
            )
        )
    )

    keywords = {
        keyword.arg: keyword.value
        for keyword in metadata_call.keywords
        if keyword.arg
    }

    assert "grade_level" in keywords
    assert "class_name" in keywords

    grade_value = keywords[
        "grade_level"
    ]

    class_value = keywords[
        "class_name"
    ]

    assert (
        isinstance(grade_value, ast.Name)
        and grade_value.id
        == "grade_level"
    )

    # The class metadata must be independently derived,
    # not populated from grade_level.
    class_names = {
        node.id
        for node in ast.walk(class_value)
        if isinstance(node, ast.Name)
    }

    assert "class_name" in class_names
    assert "grade_level" not in class_names
