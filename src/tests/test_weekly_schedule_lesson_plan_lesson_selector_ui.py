from pathlib import Path


UI = Path(
    "src/portal_v2/ui/"
    "weekly_schedule_streamlit.py"
)


def source():
    return UI.read_text(
        encoding="utf-8"
    )


def test_workspace_selects_lesson_not_individual_period():
    text = source()

    assert (
        "_lesson_plan_lesson_options_from_rows"
        in text
    )

    assert (
        '"B\\u00e0i d\\u1ea1y"'
        in text
    )

    assert (
        "selected_unit_index"
        in text
    )

    assert (
        "selected_unit"
        in text
    )

    # Transitional bridge remains until the
    # downstream DOCX workflow becomes unit-based.
    assert (
        "selected_lesson"
        in text
    )


def test_workspace_displays_lesson_summary():
    text = source()

    assert (
        "_render_selected_lesson_summary"
        in text
    )

    assert (
        '"Ti\\u1ebft PPCT"'
        in text
    )

    assert (
        '"S\\u1ed1 ti\\u1ebft"'
        in text
    )

    assert (
        '"L\\u1edbp"'
        in text
    )

    assert (
        '"**Ng\\u00e0y d\\u1ea1y**"'
        in text
    )


def test_transition_keeps_existing_workflow_contract():
    text = source()

    assert "selected_index" in text
    assert "selected_row" in text

    assert (
        '"representative_index"'
        in text
    )


def test_upload_still_happens_after_lesson_selection():
    text = source()

    assert "st.file_uploader(" in text

    assert (
        '"T\\u1ea3i gi\\u00e1o '
        '\\u00e1n Word (.docx)"'
        in text
    )


def test_new_lesson_selector_has_no_question_mark_labels():
    text = source()

    helper_start = text.index(
        "def _lesson_plan_lesson_options_from_rows("
    )

    helper_end = text.index(
        "def _lesson_plan_row_label(",
        helper_start,
    )

    helper = text[
        helper_start:
        helper_end
    ]

    assert "Ti?t" not in helper
    assert "S? ti?t" not in helper
    assert "L?p" not in helper
    assert "Ngày d?y" not in helper
