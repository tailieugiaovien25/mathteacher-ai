import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "scripts/teacher_portal/app.py"


def _radio_calls_with_key(tree, key_value):
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (
            isinstance(func, ast.Attribute)
            and func.attr == "radio"
        ):
            continue
        key_kw = next((kw for kw in node.keywords if kw.arg == "key"), None)
        if (
            key_kw is not None
            and isinstance(key_kw.value, ast.Constant)
            and key_kw.value.value == key_value
        ):
            hits.append(node)
    return hits


def test_portal_navigation_competing_default_is_resolved():
    text = APP.read_text(encoding="utf-8-sig")
    tree = ast.parse(text)
    calls = _radio_calls_with_key(tree, "portal_navigation")
    assert calls, "portal_navigation radio not found"
    # D3 resolves the previously recorded competing-default debt.
    assert all(all(kw.arg != "index" for kw in call.keywords) for call in calls)


def test_portal_navigation_is_registered_in_ownership_registry_source():
    ownership = (
        ROOT / "src/portal_v2/context/ownership.py"
    ).read_text(encoding="utf-8-sig")
    assert '"portal_navigation", None, ContextStateRole.WIDGET' in ownership
    assert '"STREAMLIT_WIDGET"' in ownership
