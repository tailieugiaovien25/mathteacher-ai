from pathlib import Path


WEEKLY = Path("src/portal_v2/ui/weekly_lesson_authoring_streamlit.py").read_text(encoding="utf-8")
APP = Path("scripts/teacher_portal/app.py").read_text(encoding="utf-8")
ROUTE = "So\u1ea1n b\u00e0i c\u00f9ng chu\u1ea9n gi\u00e1o \u00e1n V2"


def test_weekly_standardization_button_uses_hidden_v2_route():
    assert 'st.session_state["lesson_plan_group_context_v2"] = payload' in WEEKLY
    assert 'st.session_state["lesson_plan_group_navigation_target"] = target' in WEEKLY
    assert 'st.session_state["portal_navigation_request"] = navigation_target' in WEEKLY
    assert ROUTE in WEEKLY


def test_hidden_v2_route_renders_isolated_v2_page():
    assert f"elif selected == '{ROUTE}':" in APP
    assert "render_standardized_lesson_plan_authoring_v2" in APP
    assert 'current_page in (' in APP
    assert ROUTE in APP


def test_visible_menu_and_legacy_page_are_preserved():
    portal_block = APP.split("PORTAL_PAGES = (", 1)[1].split(")", 1)[0]
    assert ROUTE not in portal_block
    assert "So\u1ea1n b\u00e0i c\u00f9ng chu\u1ea9n gi\u00e1o \u00e1n" in portal_block
    assert "render_weekly_schedule_workspace" in APP
