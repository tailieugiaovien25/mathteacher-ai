from pathlib import Path
import portal_v2.ui.weekly_schedule_streamlit as module

def _source():
    return Path(module.__file__).read_text(encoding="utf-8-sig")

def test_lbg_callback_uses_canonical_emitter():
    s=_source()
    a=s.index("def _autosave_lbg_filter_context(")
    b=s.index("def _sync_lbg_week_from_loaded_data(",a)
    block=s[a:b]
    assert "_emit_canonical_week_change(" in block
    assert 'st.session_state["lbg_user_week_number"] = selected_week' not in block

def test_standardization_callback_uses_canonical_emitter():
    s=_source()
    a=s.index("def _sync_standardization_week_to_lbg(")
    b=s.index("def _",a+5)
    block=s[a:b]
    assert "_emit_canonical_week_change(" in block
    assert '"system_weekly_week_number"' not in block
    assert '"lbg_user_week_number"' not in block

def test_loaded_lbg_data_is_detector_not_writer():
    s=_source()
    a=s.index("def _sync_lbg_week_from_loaded_data(")
    b=s.index("def _sync_standardization_week_to_lbg(",a)
    block=s[a:b]
    assert "get_canonical_context(" in block
    assert "_LBG_DATA_WEEK_CONTEXT_MISMATCH_KEY" in block
    assert 'st.session_state["system_weekly_week_number"] = data_week' not in block
    assert 'st.session_state["lbg_user_week_number"] = data_week' not in block
    assert "st.session_state[_STANDARDIZATION_WEEK_KEY] = data_week" not in block

def test_mismatch_is_fail_closed():
    s=_source()
    assert "không được phép đổi Tuần hệ thống" in s
    assert "canonical_week" in s
    assert "data_week" in s

def test_emitter_requires_portal_user():
    s=_source()
    a=s.index("def _emit_canonical_week_change(")
    b=s.index("def _autosave_lbg_filter_context(",a)
    block=s[a:b]
    assert '"portal_user_id"' in block
    assert "CANONICAL_CONTEXT_USER_ID_REQUIRED" in block
    assert "apply_canonical_year_week_change(" in block
