from pathlib import Path
import ast


UI_PATH = Path(
    "src/portal_v2/ui/"
    "weekly_schedule_streamlit.py"
)


def _load_tree():
    text = UI_PATH.read_text(
        encoding="utf-8-sig"
    )
    return text, ast.parse(text)


def _function(tree, name):
    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == name
        ):
            return node

    raise AssertionError(
        f"Function not found: {name}"
    )


def _parameter_names(function):
    return {
        argument.arg
        for argument
        in function.args.args
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


def _keyword_names(call):
    return {
        keyword.arg
        for keyword in call.keywords
        if keyword.arg is not None
    }


def test_standardization_workspace_accepts_teacher_user_id():
    _, tree = _load_tree()

    function = _function(
        tree,
        "_render_lesson_plan_standardization_workspace",
    )

    assert (
        "teacher_user_id"
        in _parameter_names(function)
    )


def test_drafting_workspace_accepts_persistence_context():
    _, tree = _load_tree()

    function = _function(
        tree,
        "_render_lesson_plan_drafting_workspace",
    )

    parameters = _parameter_names(
        function
    )

    assert "teacher_user_id" in parameters
    assert "academic_year" in parameters
    assert "week_number" in parameters
    assert "selection_mode" in parameters
    assert "selection_unit_id" in parameters


def test_standardization_passes_context_to_drafting_workspace():
    _, tree = _load_tree()

    function = _function(
        tree,
        "_render_lesson_plan_standardization_workspace",
    )

    calls = _calls(
        function,
        "_render_lesson_plan_drafting_workspace",
    )

    assert len(calls) == 1

    keywords = _keyword_names(
        calls[0]
    )

    assert "selected_lesson" in keywords
    assert "teacher_user_id" in keywords
    assert "academic_year" in keywords
    assert "week_number" in keywords
    assert "selection_mode" in keywords
    assert "selection_unit_id" in keywords


def test_drafting_workspace_uses_draft_service():
    text, tree = _load_tree()

    function = _function(
        tree,
        "_render_lesson_plan_drafting_workspace",
    )

    source = ast.get_source_segment(
        text,
        function,
    )

    assert source is not None

    assert (
        "LessonPlanDraftWorkspaceService"
        in source
    )

    assert (
        "LessonPlanWorkspaceV1Service"
        in source
    )

    assert (
        "workspace_service.save("
        in source
    )

    assert (
        "workspace_service.load("
        in source
    )



def test_drafting_workspace_no_longer_claims_session_only_persistence():
    text, tree = _load_tree()

    function = _function(
        tree,
        "_render_lesson_plan_drafting_workspace",
    )

    source = ast.get_source_segment(
        text,
        function,
    )

    assert source is not None

    assert (
        "persistence inside"
        " Streamlit session state"
        not in source
    )
