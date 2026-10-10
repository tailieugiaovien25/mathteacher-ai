from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "portal_v2" / "ui" / "teaching_assistant_avatar_surface_streamlit.py"
TEACHER_APP = ROOT.parent / "scripts" / "teacher_portal" / "app.py"


def test_avatar_surface_uses_shared_teaching_session_manager():
    source = SURFACE.read_text(encoding="utf-8")
    assert "get_or_create_teaching_session" in source
    assert "teaching_session = get_or_create_teaching_session(st.session_state)" in source
    assert "controller = teaching_session.controller" in source
    assert "TeachingAssistantController(" not in source


def test_avatar_surface_executes_plan_through_session_when_active():
    source = SURFACE.read_text(encoding="utf-8")
    assert "teaching_session.execute_plan(session_plan, teacher_confirmed=True)" in source
    assert "plan_for_single_action(plan, action.action_id)" in source


def test_teacher_portal_still_dispatches_ai_teaching_assistant_route():
    source = TEACHER_APP.read_text(encoding="utf-8")
    assert 'elif selected == "AI Trợ giảng":' in source
    assert "render_teaching_assistant_avatar_surface(" in source


def test_surface_is_parseable_python():
    ast.parse(SURFACE.read_text(encoding="utf-8"))
