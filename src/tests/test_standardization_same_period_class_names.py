import ast
from pathlib import Path
from types import SimpleNamespace


UI = Path(
    "src/portal_v2/ui/weekly_schedule_streamlit.py"
)


def source() -> str:
    return UI.read_text(encoding="utf-8-sig")


def test_same_period_classes_are_collected_from_schedule_rows():
    text = source()

    assert "def _class_ids_for_same_timetable_lesson(" in text
    assert "def _rows_for_same_timetable_lesson(" in text
    assert 'getattr(row, "curriculum_period", None) != selected_period' in text
    assert "row_subject != selected_subject" in text
    assert "row_component != selected_component" in text
    assert "row_lesson_title != selected_lesson_title" in text
    assert "selected_lesson_id" not in text[
        text.index("def _class_ids_for_same_timetable_lesson("):
        text.index("def _class_display_names(")
    ]
    assert "matched_rows.append(row)" in text


def test_different_record_ids_do_not_split_classes_of_same_lesson():
    tree = ast.parse(source())
    functions = [
        node
        for node in tree.body
        if (
            isinstance(node, ast.FunctionDef)
            and node.name
            in {
                "_rows_for_same_timetable_lesson",
                "_class_ids_for_same_timetable_lesson",
            }
        )
    ]
    module = ast.Module(body=functions, type_ignores=[])
    namespace = {}
    exec(compile(module, str(UI), "exec"), namespace)
    collect = namespace["_class_ids_for_same_timetable_lesson"]

    rows = (
        SimpleNamespace(
            subject_ref="subject-math",
            component_ref="arithmetic",
            curriculum_period=1,
            lesson_id="lesson-record-6A1",
            lesson_title="Bài 1. Tập hợp",
            class_id="class-6A1",
        ),
        SimpleNamespace(
            subject_ref="subject-math",
            component_ref="arithmetic",
            curriculum_period=1,
            lesson_id="lesson-record-6A2",
            lesson_title="Bài 1. Tập hợp",
            class_id="class-6A2",
        ),
    )

    assert collect(rows, selected_row=rows[1]) == (
        "class-6A1",
        "class-6A2",
    )


def test_all_resolved_class_names_are_joined_for_display():
    text = source()

    assert "def _class_display_names(" in text
    assert 'return ", ".join(names) if names else "-"' in text
    assert "context_class = _class_display_names(" in text


def test_aggregated_class_names_flow_to_editor_document_and_storage():
    text = source()

    assert 'selected_lesson["classes"] = selected_class_ids' in text
    assert '"class_name": context_class' in text
    assert "metadata_override.get(" in text
    assert '"class_name",' in text
