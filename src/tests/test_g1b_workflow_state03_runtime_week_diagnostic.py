from pathlib import Path

SOURCE = Path("src/portal_v2/ui/weekly_lesson_authoring_streamlit.py")

def test_workflow_state03_diagnostic_is_read_only():
    text = SOURCE.read_text(encoding="utf-8")
    assert "G1B_WORKFLOW_STATE03_RUNTIME_WEEK_DIAGNOSTIC" in text
    assert "WORKFLOW-STATE-03" in text
    block = text.split("G1B_WORKFLOW_STATE03_RUNTIME_WEEK_DIAGNOSTIC", 1)[1]
    block = block.split("selected_week = int(st.session_state[_WEEK_KEY])", 1)[0]
    forbidden = (
        'st.session_state[_WEEK_KEY] =',
        'st.session_state["global_weekly_active_week_number"] =',
        'st.session_state["standardization_authoring_week_number"] =',
        'st.session_state["lbg_user_week_number"] =',
        'st.session_state["system_weekly_week_number"] =',
        "apply_canonical_year_week_change(",
        "_emit_canonical_week_change(",
    )
    for token in forbidden:
        assert token not in block

def test_workflow_state03_observes_required_week_keys():
    text = SOURCE.read_text(encoding="utf-8")
    for token in (
        "canonical_week",
        "weekly_lesson_authoring_week_number",
        "global_weekly_active_week_number",
        "standardization_authoring_week_number",
        "lbg_user_week_number",
        "system_weekly_week_number",
    ):
        assert token in text

def test_workflow_state03_uses_proven_canonical_context_module():
    text = SOURCE.read_text(encoding="utf-8")
    assert "from portal_v2.context.session_scoped_context_holder import get_canonical_context as _g1b_ws03_get_canonical_context" in text
    assert "from portal_v2.system_context import get_canonical_context" not in text
