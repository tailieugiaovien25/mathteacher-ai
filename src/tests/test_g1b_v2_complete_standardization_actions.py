from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py"
MANAGEMENT = ROOT / "src/portal_v2/ui/standardized_lesson_plan_management_streamlit.py"
APP = ROOT / "scripts/teacher_portal/app.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def test_ai_uses_existing_project_handler_and_preserves_source_copy():
    v2 = _text(V2)
    app = _text(APP)
    assert "_resolve_g1b_v2_ai_handler" in app
    assert "ai_handler=_g1b_v2_ai_handler" in app
    assert "AI kiểm tra và đề xuất" in v2
    assert "LessonPlanAiRevisionOverlay" in v2
    assert "working_content = original_content" in v2
    assert "content=working_content" in v2
    assert "file gốc vẫn được giữ nguyên" in v2


def test_merged_artifact_can_use_shared_system_save_handler():
    text = _text(MANAGEMENT)
    assert "standardized_merge_save_v5" in text
    assert "disabled=save_handler is None" in text
    assert 'artifact_file_name=str(merged["file_name"])' in text
    assert 'artifact_content=bytes(merged["content"])' in text


def test_v2_visible_text_has_no_known_mojibake_markers():
    text = _text(V2)
    for marker in ("Ã", "Ä", "Æ", "â†", "á»", "áº"):
        assert marker not in text
