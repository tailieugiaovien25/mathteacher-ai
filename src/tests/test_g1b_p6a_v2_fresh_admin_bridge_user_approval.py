from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "scripts" / "teacher_portal" / "app.py"
V2 = ROOT / "src" / "portal_v2" / "ui" / "standardized_lesson_plan_authoring_v2_streamlit.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def test_v2_direct_entry_uses_fresh_admin_runtime_bridge():
    text = _text(APP)
    assert "G1B_P6A_V2_FRESH_ADMIN_BRIDGE" in text
    assert "apply_active_admin_lesson_plan_configuration(" in text
    assert 'context.get("subject_ref")' in text
    assert 'context.get("component_ref")' in text
    assert 'st.session_state["standardization_subject_filter"] = subject_ref' in text
    assert 'st.session_state["standardization_component_filter"] = component_ref' in text
    assert "standardize_handler=_g1b_v2_standardize_with_fresh_admin_config" in text


def test_v2_clears_stale_admin_projection_before_resolve():
    text = _text(APP)
    for key in (
        "lesson_plan_admin_runtime_configuration_payload",
        "lesson_plan_admin_runtime_configuration_source",
        "lesson_plan_admin_template_profile",
        "lesson_plan_template_profile",
        "subject_lesson_plan_profile",
        "lesson_plan_admin_approval_policy",
        "lesson_plan_admin_approval_label",
        "lesson_plan_admin_approval_alignment",
        "standardization_drafting_before_monday_enabled",
        "standardization_drafting_before_monday_days",
        "standardization_approval_before_monday_days",
    ):
        assert f'"{key}"' in text


def test_v2_user_owns_only_approval_yes_no_toggle():
    app = _text(APP)
    ui = _text(V2)
    assert "G1B_P6A_V2_USER_APPROVAL_TOGGLE" in ui
    assert 'key="g1b_v2_include_approval_block"' in ui
    assert '"standardization_approval_before_monday_enabled"' in app
    assert '"g1b_v2_include_approval_block"' in app
    assert "lesson_plan_admin_approval_label" not in ui
    assert "lesson_plan_admin_approval_alignment" not in ui


def test_p6a_keeps_existing_v2_handler_and_review_isolation():
    app = _text(APP)
    assert "standardize_lesson_plan_v2_document(" in app
    assert "render_lesson_plan_teacher_review" not in app
