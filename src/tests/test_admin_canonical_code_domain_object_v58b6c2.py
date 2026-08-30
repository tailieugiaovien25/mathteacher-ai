from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = (
    ROOT / "src" / "portal_v2" / "ui" /
    "admin_canonical_code_catalog_streamlit.py"
).read_text(encoding="utf-8")

def test_admin_catalog_supports_domain_objects():
    assert "def _canonical_code_value(" in UI
    assert "getattr(item, field_name, default)" in UI

def test_admin_catalog_keeps_mapping_compatibility():
    assert "isinstance(item, dict)" in UI
    assert "item.get(field_name, default)" in UI
