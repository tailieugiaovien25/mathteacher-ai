from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "scripts" / "teacher_portal" / "app.py"


def test_v2_runtime_save_no_longer_imports_nested_weekly_helper():
    app = APP.read_text(encoding="utf-8")
    assert "_save_standardized_artifact_to_library" not in app
    assert "def _g1b_v2_save_standardized_artifact(" in app
    assert "save_handler=_g1b_v2_save_standardized_artifact" in app


def test_v2_runtime_save_reuses_document_library_upload_service():
    app = APP.read_text(encoding="utf-8")
    assert '"document_library_upload_service"' in app
    assert "DocumentUploadMetadata(" in app
    assert "upload_service.upload(" in app
    assert "selected_group_context(st.session_state)" in app
