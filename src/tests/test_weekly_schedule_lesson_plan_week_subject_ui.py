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


def test_week_subject_mode_is_supported_in_ui():
    text = _source()

    assert (
        text.count(
            "LessonPlanSelectionMode.WEEK_SUBJECT"
        )
        >= 2
    )


def test_week_subject_has_display_label():
    strings = {
        node.value
        for node in ast.walk(_tree())
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        )
    }

    assert (
        "Theo tu\u1ea7n / m\u00f4n h\u1ecdc"
        in strings
    )


def test_existing_modes_are_preserved():
    text = _source()

    for name in (
        "LESSON",
        "PERIOD",
        "TOPIC",
    ):
        assert (
            "LessonPlanSelectionMode."
            + name
            in text
        )
