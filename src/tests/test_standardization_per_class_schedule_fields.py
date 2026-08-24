import ast
from datetime import date
from pathlib import Path
from types import SimpleNamespace


UI = Path(
    "src/portal_v2/ui/weekly_schedule_streamlit.py"
)


def source() -> str:
    return UI.read_text(encoding="utf-8-sig")


def _isolated_function(name: str, namespace=None):
    tree = ast.parse(source())
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )
    scope = dict(namespace or {})
    exec(
        compile(ast.Module(body=[function], type_ignores=[]), str(UI), "exec"),
        scope,
    )
    return scope[name]


def test_timetable_period_and_date_are_formatted_for_each_class():
    display = _isolated_function(
        "_class_schedule_display_values",
        {
            "_class_display_name": lambda class_id, client=None: {
                "class-7A1": "7A1",
                "class-7A2": "7A2",
            }[class_id]
        },
    )
    rows = (
        SimpleNamespace(
            class_id="class-7A2",
            timetable_period=2,
            teaching_date=date(2026, 9, 10),
        ),
        SimpleNamespace(
            class_id="class-7A1",
            timetable_period=4,
            teaching_date=date(2026, 9, 8),
        ),
    )

    assert display(rows) == (
        "7A1: tiết 4; 7A2: tiết 2",
        "7A1: 08/09/2026; 7A2: 10/09/2026",
    )


def test_ui_uses_per_class_values_instead_of_representative_row():
    text = source()

    assert "context_timetable_period," in text
    assert "context_teaching_date_text," in text
    assert "= _class_schedule_display_values(" in text
    assert 'selected_lesson["timetable_periods_by_class"]' in text
    assert 'selected_lesson["teaching_dates_by_class"]' in text


def test_per_class_schedule_cards_show_every_class_without_ellipsis():
    text = source()
    styles = Path(
        "src/portal_v2/ui/teacher_workspace_styles.py"
    ).read_text(encoding="utf-8-sig")

    assert 'replace("; ", "<br>")' in text
    assert text.count("mt-context-item--multiline") >= 2
    assert ".mt-context-item--multiline .mt-context-value" in styles
    assert "white-space: normal;" in styles
    assert "text-overflow: clip;" in styles
