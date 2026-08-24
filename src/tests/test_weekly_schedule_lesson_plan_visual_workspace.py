import ast
from pathlib import Path


UI = Path(
    "src/portal_v2/ui/"
    "weekly_schedule_streamlit.py"
)

VIEWER = Path(
    "scripts/teacher_portal/"
    "lesson_plan_visual_viewer.py"
)


def ui_source():
    return UI.read_text(
        encoding="utf-8"
    )


def viewer_source():
    return VIEWER.read_text(
        encoding="utf-8"
    )


def test_workspace_has_class_display_resolver():
    text = ui_source()

    assert (
        "def _class_display_name("
        in text
    )

    assert (
        "_class_display_name("
        in text
    )


def test_summary_does_not_directly_display_class_id():
    text = ui_source()
    tree = ast.parse(text)

    resolver_calls = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        if not isinstance(
            node.func,
            ast.Name,
        ):
            continue

        if (
            node.func.id
            != "_class_display_name"
        ):
            continue

        resolver_calls.append(node)

    assert resolver_calls

    call_sources = [
        ast.get_source_segment(
            text,
            call,
        )
        or ""
        for call in resolver_calls
    ]

    assert any(
        (
            "class_id" in source
            or "selected_row.class_id"
            in source
        )
        for source in call_sources
    )

    assert any(
        "client=client" in source
        for source in call_sources
    )

def test_canonical_class_uses_display_name():
    text = ui_source()

    assert (
        "DocumentField.CLASS_NAME"
        in text
    )

    assert (
        "_class_display_name("
        in text
    )


def test_workspace_embeds_visual_docx_viewer():
    text = ui_source()

    assert (
        "build_document_html"
        in text
    )

    assert (
        "Xem to\\u00e0n b\\u1ed9 "
        in text
    )

    assert (
        "gi\\u00e1o \\u00e1n"
        in text
    )

    assert (
        "st.components.v1.html("
        in text
    )

def test_viewer_is_safe_to_import():
    text = viewer_source()

    assert "def main():" in text

    assert (
        'if __name__ == "__main__":'
        in text
    )


def test_viewer_renderer_remains_reusable():
    text = viewer_source()

    assert (
        "def build_document_html("
        in text
    )
