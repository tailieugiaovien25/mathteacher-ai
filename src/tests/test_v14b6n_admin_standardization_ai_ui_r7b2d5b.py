from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = ROOT / "src" / "portal_v2" / "ui" / "admin_lesson_authoring_ai_settings_streamlit.py"
CENTER = ROOT / "src" / "portal_v2" / "ui" / "admin_lesson_plan_coordination_center_streamlit.py"

def test_standardization_ai_renderer_exists():
    text = SETTINGS.read_text(encoding="utf-8-sig")
    assert "def render_admin_standardization_ai_settings" in text
    assert "updated = dict(_settings(st))" in text
    assert "document_ai_enabled" in text
    assert "document_ai_provider" in text
    assert "document_ai_model" in text

def test_admin_center_wires_renderer():
    text = CENTER.read_text(encoding="utf-8-sig")
    assert "render_admin_standardization_ai_settings(st, client=client)" in text
    assert "# Compatibility contract only: render_admin_lesson_authoring_ai_settings(st, client=client)" in text

def test_no_secret_fields_added():
    text = SETTINGS.read_text(encoding="utf-8-sig")
    assert "GEMINI_API_KEY" not in text
    assert "OPENAI_API_KEY" not in text
