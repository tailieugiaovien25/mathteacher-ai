from pathlib import Path
import portal_v2.ui.weekly_schedule_streamlit as module

def _source():
    return Path(module.__file__).read_text(encoding="utf-8-sig")

def test_workspace_uses_system_context_as_week_authority():
    s = _source()
    assert "V57-F2C5G_CANONICAL_WEEK_AUTHORITY" in s
    assert "publish_year_week_projection(" in s
    assert "SystemContext.week_number is the only business-context authority here" in s

def test_legacy_lbg_authority_comment_is_removed():
    assert "LBG is authoritative for operational metadata:" not in _source()

def test_restore_snapshot_no_longer_fans_out_week_keys():
    s = _source()
    a = s.index("restore_context = dict(")
    b = s.index("navigation_notice =", a)
    block = s[a:b]
    assert 'st.session_state["system_weekly_week_number"] = restored_week' not in block
    assert 'st.session_state["lbg_user_week_number"] = restored_week' not in block
    assert "st.session_state[_STANDARDIZATION_WEEK_KEY] = restored_week" not in block
    assert "standardization_restore_snapshot" in block

def test_standardization_pre_widget_direct_writer_removed():
    s = _source()
    marker = "V57-F2C5G: widget value is already projected from canonical"
    a = s.index(marker)
    b = s.index("st.markdown(", a)
    assert "st.session_state[" not in s[a:b]

def test_invalid_canonical_week_initializes_from_admin_week_set():
    s = _source()
    assert 'source_control="academic_week_default"' in s
    assert "int(week_numbers[0])" in s
