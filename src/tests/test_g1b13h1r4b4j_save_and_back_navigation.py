from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHORING = ROOT / "src" / "portal_v2" / "ui" / "standardized_lesson_plan_authoring_v2_streamlit.py"
APP = ROOT / "scripts" / "teacher_portal" / "app.py"

def test_verified_save_handler_is_reused():
    authoring = AUTHORING.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    assert "save_handler: Callable[..., Any] | None = None" in authoring
    assert "save_handler=save_handler" in authoring
    assert "_save_standardized_artifact_to_library" not in app
    assert "def _g1b_v2_save_standardized_artifact(" in app
    assert "save_handler=_g1b_v2_save_standardized_artifact" in app

def test_bottom_back_button_uses_existing_portal_navigation():
    authoring = AUTHORING.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    assert "# G1B_13H1R4B4J_SAVE_AND_BACK_NAV" in authoring
    assert '← Quay lại Soạn bài theo tuần' in authoring
    assert authoring.index("render_standardized_lesson_plan_management(") < authoring.index(
        "# G1B_13H1R4B4J_SAVE_AND_BACK_NAV"
    )
    assert "portal_navigation_request" in app
    assert 'Soạn bài theo tuần' in app
