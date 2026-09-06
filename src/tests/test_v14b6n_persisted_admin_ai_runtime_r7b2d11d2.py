from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COORDINATION = ROOT / "src/portal_v2/ui/admin_lesson_plan_coordination_center_streamlit.py"
APP = ROOT / "scripts/teacher_portal/app.py"
REPOSITORY = ROOT / "src/lesson_planning_v2/adapters/supabase_lesson_plan_configuration_admin_repository.py"
BRIDGE = ROOT / "src/lesson_planning_v2/services/lesson_plan_configuration_runtime_bridge.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_builder_persists_admin_ai_runtime_into_configuration_payload():
    text = _text(COORDINATION)
    assert "V14B6N_R7B2D11D2_PERSIST_ADMIN_AI_RUNTIME" in text
    assert 'payload["ai_runtime"] = {' in text
    assert '"enabled": bool(' in text
    assert '"provider": _document_ai_provider' in text
    assert '"model": _document_ai_model or None' in text
    assert text.index('payload["ai_runtime"] = {') < text.index("_g1b_payload = payload")


def test_persisted_ai_runtime_block_contains_no_credentials():
    text = _text(COORDINATION)
    start = text.index("V14B6N_R7B2D11D2_PERSIST_ADMIN_AI_RUNTIME")
    end = text.index("_g1b_payload = payload", start)
    block = text[start:end].lower()
    assert "api_key" not in block
    assert "secret" not in block
    assert "credential" not in block


def test_runtime_prefers_persisted_ai_runtime_and_keeps_session_as_fallback():
    text = _text(APP)
    assert "V14B6N_R7B2D11D2_PREFER_PERSISTED_AI_RUNTIME" in text
    assert '_persisted_runtime_payload.get("ai_runtime")' in text
    assert "and not isinstance(_persisted_ai_runtime, dict)" in text


def test_existing_draft_publish_active_flow_remains_the_persistence_path():
    repository = _text(REPOSITORY)
    bridge = _text(BRIDGE)
    assert '"configuration_payload": dict(configuration_payload)' in repository
    assert '"version_status": "PUBLISHED"' in repository
    assert 'payload["lifecycle_status"] = "ACTIVE"' in repository
    assert "payload = dict(resolved.configuration_payload)" in bridge
