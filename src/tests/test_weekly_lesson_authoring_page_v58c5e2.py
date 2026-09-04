from pathlib import Path
import ast

APP_PATH = Path("scripts/teacher_portal/app.py")
APP = APP_PATH.read_text(encoding="utf-8-sig")
PAGE = Path("src/portal_v2/ui/weekly_lesson_authoring_streamlit.py").read_text(encoding="utf-8-sig")

TREE = ast.parse(APP)
APP_STRINGS = {
    node.value
    for node in ast.walk(TREE)
    if isinstance(node, ast.Constant) and isinstance(node.value, str)
}

def test_weekly_authoring_visible():
    assert "Soạn bài theo tuần" in APP_STRINGS
    assert "render_weekly_lesson_authoring_page" in APP

def test_standardization_renamed():
    assert "Soạn bài cùng chuẩn giáo án" in APP_STRINGS

def test_ai_preserved_structurally():
    assert "lesson_authoring_ai_streamlit" in APP
    assert APP.count("render_lesson_authoring_ai_page") >= 2

def test_no_new_context_authority():
    # V58-C5E4 intentionally removes the large legacy workspace.
    assert "render_weekly_schedule_workspace" not in PAGE
    assert "apply_canonical_year_week_change" in PAGE
    assert "_sync_standardization_week_to_lbg" not in PAGE
    assert "_v58_c5b2_shadow_lesson_plan_groups" not in PAGE
    assert "ContextChange(" not in PAGE
    assert "_emit_canonical_week_change" not in PAGE
    assert "BY_GRADE" not in PAGE
