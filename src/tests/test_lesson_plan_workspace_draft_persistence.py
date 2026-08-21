from pathlib import Path
import ast


ROOT = Path("src/lesson_planning_v2")

MODEL = ROOT / "workspace_draft.py"
REPOSITORY = (
    ROOT
    / "repositories"
    / "lesson_plan_workspace_draft_repository.py"
)
SERVICE = (
    ROOT
    / "services"
    / "lesson_plan_draft_workspace_service.py"
)


def _text(path):
    assert path.exists(), f"missing file: {path}"
    return path.read_text(
        encoding="utf-8-sig"
    )


def _tree(path):
    return ast.parse(
        _text(path)
    )


def _classes(path):
    return {
        node.name
        for node in ast.walk(_tree(path))
        if isinstance(node, ast.ClassDef)
    }


def test_workspace_draft_model_exists():
    assert MODEL.exists()

    assert (
        "LessonPlanWorkspaceDraft"
        in _classes(MODEL)
    )


def test_workspace_draft_has_teacher_owned_identity():
    text = _text(MODEL)

    for field in (
        "draft_id",
        "teacher_user_id",
        "academic_year",
        "week_number",
        "subject_ref",
        "selection_mode",
        "selection_unit_id",
    ):
        assert field in text


def test_workspace_draft_has_editable_content():
    text = _text(MODEL)

    for field in (
        "objectives_text",
        "materials_text",
        "teaching_process_text",
    ):
        assert field in text


def test_workspace_draft_repository_contract_exists():
    assert REPOSITORY.exists()

    classes = _classes(REPOSITORY)

    assert (
        "LessonPlanWorkspaceDraftRepository"
        in classes
    )


def test_repository_supports_save_and_get():
    text = _text(REPOSITORY)

    assert "def save(" in text
    assert "def get(" in text


def test_repository_is_storage_neutral():
    text = _text(REPOSITORY).lower()

    assert "supabase" not in text
    assert ".table(" not in text
    assert ".upsert(" not in text
    assert "streamlit" not in text


def test_workspace_service_exists():
    assert SERVICE.exists()

    assert (
        "LessonPlanDraftWorkspaceService"
        in _classes(SERVICE)
    )


def test_workspace_service_depends_on_repository_port():
    text = _text(SERVICE)

    assert (
        "LessonPlanWorkspaceDraftRepository"
        in text
    )


def test_workspace_service_can_save_draft():
    text = _text(SERVICE)

    assert "def save_draft(" in text


def test_workspace_service_has_no_streamlit_or_supabase_dependency():
    text = _text(SERVICE).lower()

    assert "streamlit" not in text
    assert "supabase" not in text
    assert ".table(" not in text


def test_existing_canonical_lesson_plan_builder_is_not_modified():
    builder = _text(
        ROOT
        / "builders"
        / "lesson_plan_builder.py"
    )

    assert "class LessonPlanDraft" in builder
    assert "class LessonPlanBuilder" in builder
