from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEEKLY = ROOT / "src/portal_v2/ui/weekly_schedule_streamlit.py"
SERVICE = ROOT / "src/lesson_planning_v2/services/lesson_plan_document_processing_service.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def test_r7b2b_application_boundary_resolves_admin_runtime():
    text = _text(WEEKLY)
    assert "V14B6N_R7B2B_ADMIN_AI_APPLICATION_BOUNDARY" in text
    assert "resolve_document_runtime_config_from_admin_payload" in text
    assert "lesson_plan_admin_runtime_configuration_payload" in text
    assert "build_document_analyzer(" in text


def test_r7b2b_reads_only_selected_provider_secret_transiently():
    text = _text(WEEKLY)
    assert '"gemini": "GEMINI_API_KEY"' in text
    assert '"openai": "OPENAI_API_KEY"' in text
    assert "credentials = {" in text
    assert "st.session_state[secret_name]" not in text
    assert 'st.session_state["GEMINI_API_KEY"]' not in text
    assert 'st.session_state["OPENAI_API_KEY"]' not in text


def test_r7b2b_processing_service_has_optional_analyzer_dependency():
    text = _text(SERVICE)
    assert "document_analyzer=None" in text
    assert "self._document_analyzer = document_analyzer" in text


def test_r7b2b_document_intelligence_is_read_only_advisory():
    text = _text(SERVICE)
    assert "V14B6N_R7B2B_DOCUMENT_INTELLIGENCE_READ_ONLY" in text
    assert "LessonPlanIntelligencePreviewService(" in text
    assert ".preview(source=working_source)" in text
    assert "document_analysis = intelligence_preview.analysis" in text


def test_r7b2b_ai_failure_does_not_abort_standardization():
    text = _text(SERVICE)
    assert "except Exception as error:" in text
    assert "document_ai_failed = True" in text
    assert "document_intelligence_error = type(error).__name__" in text


def test_r7b2b_standardizer_remains_docx_mutation_owner():
    text = _text(SERVICE)
    intelligence_at = text.index(
        "V14B6N_R7B2B_DOCUMENT_INTELLIGENCE_READ_ONLY"
    )
    standardizer_at = text.index("LessonPlanWordStandardizer(")
    assert intelligence_at < standardizer_at
    assert "document_analysis=document_analysis" in text


def test_r7b2b_pipeline_evidence_exposes_ai_status_without_secret():
    text = _text(WEEKLY)
    assert '"document_ai_used"' in text
    assert '"document_ai_failed"' in text
    assert '"document_intelligence_error"' in text
    evidence_start = text.index(
        "G1B_A5E_UPLOAD_EVIDENCE_SIDE_CHANNEL"
    )
    evidence_window = text[evidence_start:evidence_start + 1600]
    assert "GEMINI_API_KEY" not in evidence_window
    assert "OPENAI_API_KEY" not in evidence_window
