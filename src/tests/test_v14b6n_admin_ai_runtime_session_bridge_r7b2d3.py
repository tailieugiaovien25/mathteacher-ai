from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADMIN_UI = ROOT / "src" / "portal_v2" / "ui" / "admin_lesson_authoring_ai_settings_streamlit.py"
APP = ROOT / "scripts" / "teacher_portal" / "app.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def test_admin_ui_has_safe_document_ai_provider_controls():
    text = _text(ADMIN_UI)
    assert '"document_ai_enabled": False' in text
    assert '"document_ai_provider": "gemini"' in text
    assert '"document_ai_model": ""' in text
    assert '"Bật AI phân tích tài liệu khi Chuẩn hóa giáo án"' in text
    assert '"Nhà cung cấp AI cho Chuẩn hóa giáo án"' in text


def test_admin_ui_does_not_capture_api_keys():
    text = _text(ADMIN_UI)
    assert "GEMINI_API_KEY" not in text
    assert "OPENAI_API_KEY" not in text
    assert "api_key" not in text.lower()


def test_admin_save_persists_only_runtime_choices_in_session():
    text = _text(ADMIN_UI)
    assert '"document_ai_enabled": bool(document_ai_enabled)' in text
    assert '"document_ai_provider": str(document_ai_provider).strip().lower()' in text
    assert '"document_ai_model": str(document_ai_model or "").strip()' in text
    assert "st.session_state[_STATE_KEY]" in text


def test_app_overlays_canonical_ai_runtime_after_fresh_admin_config():
    text = _text(APP)
    marker = text.index("V14B6N_R7B2D3_ADMIN_AI_RUNTIME_SESSION_BRIDGE")
    apply_at = text.rfind("apply_active_admin_lesson_plan_configuration(", 0, marker)
    standardize_at = text.index("standardize_lesson_plan_v2_document(", marker)
    assert apply_at >= 0
    assert apply_at < marker < standardize_at
    window = text[marker:standardize_at]
    assert 'runtime_payload["ai_runtime"] = {' in window
    assert '"enabled": bool(' in window
    assert '"provider": document_ai_provider' in window
    assert '"model": document_ai_model or None' in window


def test_app_bridge_does_not_persist_or_route_secrets():
    text = _text(APP)
    marker = text.index("V14B6N_R7B2D3_ADMIN_AI_RUNTIME_SESSION_BRIDGE")
    standardize_at = text.index("standardize_lesson_plan_v2_document(", marker)
    window = text[marker:standardize_at]
    assert "GEMINI_API_KEY" not in window
    assert "OPENAI_API_KEY" not in window
    assert "st.secrets" not in window


def test_invalid_session_provider_is_normalized_without_auto_fallback_chain():
    text = _text(APP)
    marker = text.index("V14B6N_R7B2D3_ADMIN_AI_RUNTIME_SESSION_BRIDGE")
    standardize_at = text.index("standardize_lesson_plan_v2_document(", marker)
    window = text[marker:standardize_at]
    assert 'document_ai_provider not in {"gemini", "openai"}' in window
    assert 'document_ai_provider = "gemini"' in window
    assert "fallback_to_openai" not in window
    assert "fallback_to_gemini" not in window


def test_bridge_remains_session_only_and_requires_no_database_write():
    admin = _text(ADMIN_UI)
    app = _text(APP)
    assert "Supabase" not in admin
    assert "repository" not in admin.lower()
    marker = app.index("V14B6N_R7B2D3_ADMIN_AI_RUNTIME_SESSION_BRIDGE")
    standardize_at = app.index("standardize_lesson_plan_v2_document(", marker)
    window = app[marker:standardize_at]
    assert "insert(" not in window
    assert "update(" not in window
    assert "upsert(" not in window
