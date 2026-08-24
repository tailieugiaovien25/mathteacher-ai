import ast
from pathlib import Path


UI = Path(
    "src/portal_v2/ui/weekly_schedule_streamlit.py"
)


def _source() -> str:
    return UI.read_text(
        encoding="utf-8"
    )


def test_lesson_plan_workspace_exists():
    source = _source()

    assert (
        "def _render_lesson_plan_standardization_workspace("
        in source
    )

    assert (
        "def _lesson_plan_row_label("
        in source
    )


def test_lesson_plan_workspace_uses_schedule_rows():
    source = _source()

    assert "view.rows" in source
    assert "row.teaching_date" in source
    assert "row.timetable_period" in source
    assert "row.class_id" in source
    assert "row.curriculum_period" in source
    assert "row.lesson_title" in source


def test_lesson_plan_workspace_accepts_docx():
    source = _source()
    tree = ast.parse(source)

    uploader_calls = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        if not isinstance(
            node.func,
            ast.Attribute,
        ):
            continue

        if node.func.attr != "file_uploader":
            continue

        uploader_calls.append(node)

    assert uploader_calls

    has_docx = False

    for call in uploader_calls:
        for keyword in call.keywords:
            if keyword.arg != "type":
                continue

            segment = ast.get_source_segment(
                source,
                keyword.value,
            )

            if (
                segment
                and "docx" in segment.casefold()
            ):
                has_docx = True

    assert has_docx

    assert (
        "uploaded.getvalue()"
        in source
    )

def test_lesson_plan_workspace_is_rendered_from_lbg():
    source = _source()

    assert (
        "_render_lesson_plan_standardization_workspace("
        in source
    )


def test_ui_delegates_document_processing():
    source = _source()

    assert (
        "LessonPlanDocumentProcessingService("
        in source
    )

    assert (
        "LessonPlanDocumentPipeline("
        not in source
    )

    assert (
        "LessonPlanWordStandardizer"
        not in source
    )

    assert (
        "TemporaryDirectory("
        not in source
    )

    assert (
        ".write_bytes("
        not in source
    )
