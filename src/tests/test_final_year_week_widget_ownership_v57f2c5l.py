from pathlib import Path
import portal_v2.ui.weekly_schedule_streamlit as module

def _source():
    return Path(module.__file__).read_text(encoding="utf-8-sig")

def test_academic_year_widget_emits_canonical_change():
    s = _source()
    assert 'changed_field == "Năm học"' in s
    assert 'field="academic_year"' in s
    assert 'source_control="system_weekly_academic_year"' in s

def test_academic_year_widget_has_no_competing_value_default():
    s = _source()
    a = s.index("academic_year = st.text_input(", s.index("with year_column:"))
    b = s.index(").strip()", a)
    block = s[a:b]
    assert "value=" not in block
    assert 'key="system_weekly_academic_year"' in block

def test_legacy_lbg_direct_mirror_writer_removed():
    s = _source()
    assert 'st.session_state[\n            "lbg_user_week_number"\n        ] = int(week_number)' not in s
    assert "No direct mirror writer is allowed here." in s

def test_legacy_lbg_week_widget_emits_canonical_change():
    s = _source()
    assert "def _sync_legacy_lbg_week_to_canonical()" in s
    assert 'source_control="lbg_user_week_number"' in s
    assert "on_change=_sync_legacy_lbg_week_to_canonical" in s

def test_all_business_week_widget_callbacks_use_canonical_emitters():
    s = _source()
    assert "on_change=_autosave_lbg_filter_context" in s
    assert "_sync_standardization_week_to_lbg" in s
    assert "_sync_legacy_lbg_week_to_canonical" in s
