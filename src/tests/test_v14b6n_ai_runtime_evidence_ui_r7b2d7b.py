from pathlib import Path


SOURCE = Path(
    "src/portal_v2/ui/"
    "standardized_lesson_plan_authoring_v2_streamlit.py"
)


def _block() -> str:
    text = SOURCE.read_text(encoding="utf-8")
    start = text.index(
        "# V14B6N_R7B2D7B_AI_RUNTIME_EVIDENCE_UI"
    )
    end = text.index(
        "# V14B6N_R7B2D7B_AI_RUNTIME_EVIDENCE_UI_END"
    )
    return text[start:end]


def test_r7b2d7b_reads_existing_pipeline_ai_evidence():
    block = _block()

    assert '"_g1b_v2_pipeline_evidence"' in block
    assert '"document_ai_used"' in block
    assert '"document_ai_failed"' in block
    assert '"document_intelligence_error"' in block
    assert '"document_analysis"' in block


def test_r7b2d7b_is_read_only_runtime_evidence_ui():
    block = _block()

    assert "AI phân tích tài liệu - Bằng chứng runtime" in block
    assert "ĐÃ SỬ DỤNG AI" in block
    assert "KHÔNG SỬ DỤNG AI" in block
    assert "GẶP LỖI" in block

    assert "st.session_state[" not in block
    assert "OPENAI_API_KEY" not in block
    assert "GEMINI_API_KEY" not in block
    assert "st.secrets" not in block


def test_r7b2d7b_provider_model_only_come_from_runtime_pipeline_evidence():
    block = _block().lower()

    assert "google gemini" not in block
    assert "openai" not in block
    assert '"_g1b_v2_pipeline_evidence"' in block
    assert '"document_ai_provider"' in block
    assert '"document_ai_model"' in block
    assert "admin_lesson_authoring_ai_settings_v1" not in block
    assert "document_ai_enabled" not in block
    assert "st.secrets" not in block


def test_r7b2d7b_keeps_ai_evidence_separate_from_audit_gate():
    text = SOURCE.read_text(encoding="utf-8")

    ai_pos = text.index(
        "# V14B6N_R7B2D7B_AI_RUNTIME_EVIDENCE_UI"
    )
    audit_pos = text.index(
        "# G1B_ENGLISH_PILOT01_A5J2A_AUDIT_EXPLAINABILITY"
    )

    assert ai_pos < audit_pos
