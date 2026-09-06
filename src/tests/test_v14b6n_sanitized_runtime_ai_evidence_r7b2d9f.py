from pathlib import Path

WEEKLY = Path("src/portal_v2/ui/weekly_schedule_streamlit.py")
UI = Path(
    "src/portal_v2/ui/"
    "standardized_lesson_plan_authoring_v2_streamlit.py"
)
R7B2D7B_TEST = Path(
    "src/tests/test_v14b6n_ai_runtime_evidence_ui_r7b2d7b.py"
)


def test_d9f_runtime_request_evidence_is_sanitized():
    text = WEEKLY.read_text(encoding="utf-8")

    assert "V14B6N_R7B2D9F_SANITIZED_AI_REQUEST_EVIDENCE" in text
    assert "V14B6N_R7B2D9F_PIPELINE_AI_REQUEST_EVIDENCE" in text
    assert '"document_ai_requested"' in text
    assert '"document_ai_provider"' in text
    assert '"document_ai_model"' in text
    assert '"document_ai_credential_configured"' in text


def test_d9f_pipeline_evidence_has_no_secret_material():
    text = WEEKLY.read_text(encoding="utf-8")

    start = text.index("V14B6N_R7B2D9F_PIPELINE_AI_REQUEST_EVIDENCE")
    block = text[start:start + 2800]

    assert "secret_value" not in block
    assert "GEMINI_API_KEY" not in block
    assert "OPENAI_API_KEY" not in block


def test_d9f_ui_reads_provider_and_model_only_from_pipeline_evidence():
    text = UI.read_text(encoding="utf-8")

    start = text.index("# V14B6N_R7B2D7B_AI_RUNTIME_EVIDENCE_UI")
    end = text.index("# V14B6N_R7B2D7B_AI_RUNTIME_EVIDENCE_UI_END")
    block = text[start:end]

    assert '"_g1b_v2_pipeline_evidence"' in block
    assert '"document_ai_provider"' in block
    assert '"document_ai_model"' in block
    assert "admin_lesson_authoring_ai_settings_v1" not in block
    assert "st.secrets" not in block
    assert "GEMINI_API_KEY" not in block
    assert "OPENAI_API_KEY" not in block


def test_d9f_stale_test_was_narrowed_not_removed():
    text = R7B2D7B_TEST.read_text(encoding="utf-8")

    assert (
        "def test_r7b2d7b_provider_model_only_come_from_runtime_pipeline_evidence():"
        in text
    )
    assert '"document_ai_provider"' in text
    assert '"document_ai_model"' in text
    assert "admin_lesson_authoring_ai_settings_v1" in text
    assert "st.secrets" in text