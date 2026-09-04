from pathlib import Path


ROOT = Path("src")


def test_standardizer_emits_events_at_real_processing_boundaries():
    text = (ROOT / "document_standardization/lesson_plan_standardizer.py").read_text(encoding="utf-8")
    for code in (
        "CONFIG", "PAGE", "FONT", "SPACING", "TABLE", "ROW",
        "FORMULA_FONT", "FORMULA_VALUE", "INTEGRITY", "GATE", "RELEASE",
    ):
        assert f'emit("{code}"' in text
    assert "progress_callback" in text
    assert "self._evaluate_format_compliance" in text


def test_progress_callback_crosses_every_runtime_boundary():
    files = (
        "document_standardization/lesson_plan_document_pipeline.py",
        "lesson_planning_v2/services/lesson_plan_document_processing_service.py",
        "portal_v2/ui/weekly_schedule_streamlit.py",
        "portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py",
    )
    for relative in files:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "progress_callback" in text, relative


def test_monitor_does_not_claim_intermediate_docx_is_final():
    text = (ROOT / "portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py").read_text(encoding="utf-8")
    assert "Quá trình tạo bản xem:" in text
    assert "_render_document(" in text
    assert 'checks["RELEASE"] = "pass" if final_status == "PASS" else "blocked"' in text
