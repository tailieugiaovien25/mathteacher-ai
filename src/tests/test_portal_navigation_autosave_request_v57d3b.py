from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "scripts/teacher_portal/app.py"

def _function_source(name: str) -> str:
    text = APP.read_text(encoding="utf-8-sig")
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            lines = text.splitlines()
            return "\n".join(lines[node.lineno - 1:node.end_lineno])
    raise AssertionError(name)

def test_autosave_callback_queues_navigation_request_from_widget_value():
    source = _function_source("_autosave_before_portal_navigation")
    assert 'session_state["portal_navigation_request"] = next_page' in source
    assert 'session_state.get("portal_navigation", previous_page)' in source

def test_autosave_still_preserves_existing_working_contexts():
    source = _function_source("_autosave_before_portal_navigation")
    assert "lesson_authoring_working_context" in source
    assert "teacher_timetable_autosaved_draft" in source
    assert "lbg_autosaved_filter_context" in source
    assert "portal_navigation_notice" in source

def test_navigation_request_resolver_remains_single_writer_for_derived_page():
    text = APP.read_text(encoding="utf-8-sig")
    assert text.count('pop("portal_navigation_request", None)') == 1
    resolver = _function_source("_resolve_portal_navigation_request")
    assert 'session_state["portal_page"] = requested' in resolver

def test_sidebar_navigation_keeps_autosave_callback():
    text = APP.read_text(encoding="utf-8-sig")
    assert "on_change=_autosave_before_portal_navigation" in text
    assert 'key="portal_navigation"' in text
