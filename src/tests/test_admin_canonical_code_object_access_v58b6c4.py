from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = (
    ROOT / "src" / "portal_v2" / "ui" /
    "admin_canonical_code_catalog_streamlit.py"
).read_text(encoding="utf-8")

def test_only_compatibility_helper_uses_dot_get():
    get_lines = [line.strip() for line in UI.splitlines() if ".get(" in line]
    assert "return item.get(field_name, default)" in get_lines
    assert not any("_canonical_code_value(" in line and ".get(" in line for line in get_lines)

def test_domain_object_safe_accessor_is_used():
    assert '_canonical_code_value(r, "namespace"' in UI
    assert '_canonical_code_value(r, "status")' in UI
    assert '_canonical_code_value(target, "namespace")' in UI
    assert '_canonical_code_value(target, "metadata")' in UI
