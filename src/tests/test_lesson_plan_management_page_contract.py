from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "scripts" / "teacher_portal" / "app.py"
UI = (
    ROOT
    / "src"
    / "portal_v2"
    / "ui"
    / "weekly_schedule_streamlit.py"
)


def test_management_page_is_in_navigation_and_wired():
    app = APP.read_text(encoding="utf-8")

    assert "'Qu\\u1ea3n l\\xfd gi\\xe1o \\xe1n'" in app
    assert "render_lesson_plan_management_workspace," in app
    assert "render_lesson_plan_management_workspace(" in app


def test_five_actions_render_only_on_management_page():
    ui = UI.read_text(encoding="utf-8")

    assert ui.count(
        "    _render_standardization_action_flow()\n"
    ) == 1
    management_start = ui.index(
        "def render_lesson_plan_management_workspace("
    )
    authoring_start = ui.index(
        "def render_lesson_authoring_tools_workspace("
    )
    management = ui[management_start:authoring_start]
    assert "_render_standardization_action_flow()" in management


def test_actions_keep_original_keys_and_targets():
    ui = UI.read_text(encoding="utf-8")
    pairs = (
        ("standardization_action_upload", "upload-lesson-plan"),
        ("standardization_action_create", "standardize-lesson-plan"),
        (
            "standardization_action_preview",
            "preview-standardized-lesson-plan",
        ),
        (
            "standardization_action_save",
            "save-standardized-lesson-plan",
        ),
        (
            "standardization_action_download",
            "download-standardized-lesson-plan",
        ),
    )
    for key, target in pairs:
        assert key in ui
        assert target in ui


def test_action_callback_preserves_context_and_navigates():
    ui = UI.read_text(encoding="utf-8")
    assert "def _activate_standardization_action(action: str)" in ui
    assert "lesson_plan_standardization_action" in ui
    assert "lesson_plan_management_pending_action" in ui
    assert 'st.session_state["portal_navigation_request"]' in ui
    assert "on_click=_activate_standardization_action" in ui
    assert "args=(action,)" in ui


def test_pending_action_scrolls_after_standardization_page_renders():
    ui = UI.read_text(encoding="utf-8")
    table_call = ui.rindex("    _render_lbg_table(")
    pending_call = ui.rindex(
        "    _render_pending_standardization_target()"
    )

    assert pending_call > table_call
    assert "element.scrollIntoView" in ui


def test_protected_page_renderers_remain_wired():
    app = APP.read_text(encoding="utf-8")

    assert "render_lesson_authoring_ai_page(" in app
    assert "render_weekly_schedule_and_equipment_workspace(" in app
    assert "render_lesson_authoring_tools_workspace(" in app
