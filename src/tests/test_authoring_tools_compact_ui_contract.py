from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_PATH = ROOT / "scripts" / "teacher_portal" / "app.py"
UI_PATH = (
    ROOT
    / "src"
    / "portal_v2"
    / "ui"
    / "weekly_schedule_streamlit.py"
)


def test_abandoned_compact_feature_is_not_enabled_by_pages():
    app_text = APP_PATH.read_text(encoding="utf-8")
    ui_text = UI_PATH.read_text(encoding="utf-8")

    app_route_start = app_text.index(
        "elif selected == 'Chu\\u1ea9n h\\xf3a gi\\xe1o \\xe1n':"
    )
    app_route_end = app_text.index(
        "elif selected == 'So\\u1ea1n b\\xe0i c\\xf9ng AI':",
        app_route_start,
    )
    app_route = app_text[app_route_start:app_route_end]

    authoring_start = ui_text.index(
        "def render_lesson_authoring_tools_workspace("
    )
    authoring_end = ui_text.index(
        "def render_weekly_schedule_workspace(",
        authoring_start,
    )
    authoring_route = ui_text[authoring_start:authoring_end]

    assert "compact_setup_ui=True" not in app_route
    assert "compact_setup_ui=True" not in authoring_route


def test_other_page_routes_remain_present():
    text = APP_PATH.read_text(encoding="utf-8")

    assert "render_lesson_authoring_ai_page(" in text
    assert "render_weekly_schedule_and_equipment_workspace(" in text

