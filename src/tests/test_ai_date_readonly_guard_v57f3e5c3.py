from pathlib import Path
import ast

SOURCE_PATH = Path("src/portal_v2/ui/lesson_authoring_ai_streamlit.py")
SOURCE = SOURCE_PATH.read_text(encoding="utf-8-sig")
TREE = ast.parse(SOURCE)

def _segment(name):
    for node in TREE.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return "\n".join(
                SOURCE.splitlines()[node.lineno - 1: node.end_lineno]
            )
    raise AssertionError("missing function: " + name)

def test_context_editor_has_no_editable_date_input():
    segment = _segment("_context_editor")
    assert ".date_input(" not in segment
    assert "Ngày thực hiện" not in segment
    assert "Ngày dạy" in segment
    assert "disabled=True" in segment

def test_teaching_date_is_read_from_context_only():
    segment = _segment("_context_editor")
    assert 'teaching_date = context.get("teaching_date")' in segment
    assert "teaching_date=teaching_date" not in segment

def test_updated_context_preserves_existing_date_without_ai_rewrite():
    segment = _segment("_context_editor")
    assert "updated = dict(context)" in segment
    assert "updated.update(" in segment
    assert "teaching_date=teaching_date" not in segment

def test_schedule_selector_still_derives_date_from_authoritative_row():
    segment = _segment("_schedule_context_selector")
    assert "teaching_date=getattr(row" in segment

def test_catalog_can_keep_readonly_provenance_copy():
    segment = _segment("_save_to_management_catalog")
    assert "teaching_date" in segment
    assert "drafting_date" in segment

def test_no_ai_ngay_soan_editable_widget():
    for line in SOURCE.splitlines():
        if ".date_input(" in line:
            assert "Ngày soạn" not in line
