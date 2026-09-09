from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "src/portal_v2/ui/weekly_lesson_authoring_streamlit.py"


def _occurrence_payload_keys():
    tree = ast.parse(TARGET.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name != "_group_context_payload":
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            function = child.func
            if not (
                isinstance(function, ast.Attribute)
                and function.attr == "append"
                and isinstance(function.value, ast.Name)
                and function.value.id == "occurrences"
                and child.args
                and isinstance(child.args[0], ast.Dict)
            ):
                continue
            payload = child.args[0]
            return tuple(
                key.value
                for key in payload.keys
                if isinstance(key, ast.Constant) and isinstance(key.value, str)
            )
    raise AssertionError("occurrences.append mapping not found")


def test_occurrence_payload_preserves_existing_contract_and_adds_repair_fields():
    keys = _occurrence_payload_keys()
    assert keys[:5] == (
        "class_id",
        "class_display",
        "teaching_date",
        "timetable_period",
        "curriculum_period",
    )
    assert keys[-2:] == ("session", "period_in_lesson")
    assert len(keys) == 7


def test_session_is_serialized_and_schema_version_remains_backward_compatible():
    source = TARGET.read_text(encoding="utf-8")
    assert "R4A2C2B2C2A_REPAIR_CONTEXT_PAYLOAD_FIELDS" in source
    assert 'getattr(item, "session", None)' in source
    assert '"period_in_lesson": getattr(item, "period_in_lesson", None)' in source
    assert '"schema_version": 1' in source
