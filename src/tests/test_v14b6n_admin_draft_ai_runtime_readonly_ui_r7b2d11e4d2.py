from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "src/portal_v2/ui/admin_lesson_plan_coordination_center_streamlit.py"


def test_readonly_draft_ai_runtime_ui_uses_existing_authenticated_version_rows():
    text = TARGET.read_text(encoding="utf-8")
    assert "V14B6N_R7B2D11E4D2_READONLY_DRAFT_AI_RUNTIME" in text
    assert 'version_by_id[readonly_draft_id].get(' in text
    assert '"configuration_payload"' in text
    assert 'readonly_payload.get("ai_runtime")' in text


def test_readonly_draft_ai_runtime_ui_exposes_only_sanitized_evidence():
    text = TARGET.read_text(encoding="utf-8")
    marker = text.index("V14B6N_R7B2D11E4D2_READONLY_DRAFT_AI_RUNTIME")
    end = text.index("with st.expander(\"Chỉnh sửa phiên bản đang soạn\"", marker)
    block = text[marker:end]
    for label in (
        "AI_RUNTIME_PRESENT:",
        "ENABLED:",
        "PROVIDER:",
        "MODEL:",
        "CREDENTIAL_FIELD_PRESENT:",
    ):
        assert label in block
    assert "st.json(readonly_ai_runtime)" not in block
    assert "st.write(readonly_ai_runtime)" not in block


def test_readonly_block_contains_no_database_write_or_publish_calls():
    text = TARGET.read_text(encoding="utf-8")
    marker = text.index("V14B6N_R7B2D11E4D2_READONLY_DRAFT_AI_RUNTIME")
    end = text.index("with st.expander(\"Chỉnh sửa phiên bản đang soạn\"", marker)
    block = text[marker:end]
    for forbidden in (
        ".insert(", ".update(", ".delete(",
        "service.publish(", "activate_published_version(",
        "update_draft(", "create_next_draft_version(",
    ):
        assert forbidden not in block
