from pathlib import Path


UI = Path(
    "src/portal_v2/ui/"
    "weekly_schedule_streamlit.py"
)


def source():
    return UI.read_text(
        encoding="utf-8"
    )


def test_ui_has_generic_selection_mode():
    text = source()

    assert (
        "LessonPlanSelectionMode"
        in text
    )

    assert (
        "LessonPlanUnitSelectorService"
        in text
    )

    assert (
        '"C\\u00e1ch ch\\u1ecdn '
        'n\\u1ed9i dung "'
        in text
    )


def test_ui_supports_lesson_period_topic():
    text = source()

    assert (
        "LessonPlanSelectionMode.LESSON"
        in text
    )

    assert (
        "LessonPlanSelectionMode.PERIOD"
        in text
    )

    assert (
        "LessonPlanSelectionMode.TOPIC"
        in text
    )


def test_ui_has_teacher_friendly_mode_labels():
    text = source()

    assert '"Theo b\\u00e0i"' in text
    assert '"Theo ti\\u1ebft"' in text

    assert (
        '"Theo ch\\u1ee7 \\u0111\\u1ec1"'
        in text
    )


def test_ui_keeps_existing_workflow_compatibility():
    text = source()

    assert "selected_lesson" in text
    assert "selected_index" in text
    assert "selected_row" in text
