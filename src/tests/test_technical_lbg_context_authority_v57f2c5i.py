from pathlib import Path
import portal_v2.ui.weekly_schedule_streamlit as module

def _source():
    return Path(module.__file__).read_text(encoding="utf-8-sig")

def test_last_updated_week_is_cache_only_not_selector_restore():
    s = _source()
    assert "last-updated week is cache metadata only" in s
    assert 'st.session_state["system_weekly_week_number"] = int(' not in s

def test_persisted_schedule_bootstrap_does_not_publish_active_year_week():
    s = _source()
    marker = "V57-F2C5I: persisted schedule discovery may"
    a = s.index(marker)
    b = s.index("_bootstrap_generation =", a)
    block = s[a:b]
    assert "_ACTIVE_ACADEMIC_YEAR_KEY" not in block
    assert "_ACTIVE_WEEK_NUMBER_KEY" not in block
    assert '"system_weekly_week_number"' not in block
    assert "persisted_schedule_bootstrap" in block

def test_exact_week_read_updates_view_cache_only():
    s = _source()
    marker = "V57-F2C5I: exact-week read updates view/cache only."
    a = s.index(marker)
    b = s.index("else:", a)
    block = s[a:b]
    assert "_ACTIVE_ACADEMIC_YEAR_KEY" not in block
    assert "_ACTIVE_WEEK_NUMBER_KEY" not in block
    assert "_ACTIVE_VIEW_KEY" in block

def test_persist_result_does_not_become_context_authority():
    s = _source()
    marker = "V57-F2C5I: persistence publishes schedule/view metadata"
    a = s.index(marker)
    b = s.index("_LBG_CONTEXT_SNAPSHOT_KEY", a)
    block = s[a:b]
    assert "_ACTIVE_ACADEMIC_YEAR_KEY" not in block
    assert "_ACTIVE_WEEK_NUMBER_KEY" not in block
    assert "_ACTIVE_SCHEDULE_ID_KEY" in block
    assert "_ACTIVE_VIEW_KEY" in block

def test_last_updated_week_remains_metadata_after_successful_persist():
    s = _source()
    assert '"_system_weekly_last_updated_week"' in s
    assert "Remember only a successfully persisted" in s
