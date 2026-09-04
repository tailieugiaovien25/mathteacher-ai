from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APPLIER = ROOT / "src/document_standardization/lesson_plan_document_context_applier.py"
SERVICE = ROOT / "src/lesson_planning_v2/services/lesson_plan_document_processing_service.py"

def _text(path):
    return path.read_text(encoding="utf-8-sig")

def test_retired_context_identity_diagnostic_stays_removed():
    text = _text(APPLIER)
    assert "G1B_13H1R4B5M_CONTEXT_IDENTITY_DIAGNOSTIC" not in text
    assert "context must be ScheduledLessonContext" in text
    assert "G1B_13H1R4B5S4_REHYDRATE_STALE_CONTEXT" in text

def test_processing_context_trace_marker_is_present():
    text = _text(SERVICE)
    assert "G1B_13H1R4B5M_PROCESSING_CONTEXT_TRACE" in text
    assert "stashed_context_type = type(context)" in text
