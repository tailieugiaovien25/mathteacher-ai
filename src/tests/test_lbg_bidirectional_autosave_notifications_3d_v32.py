from pathlib import Path


WEEKLY = Path("src/portal_v2/ui/weekly_schedule_streamlit.py")
AI = Path("src/portal_v2/ui/lesson_authoring_ai_streamlit.py")


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _function(text: str, name: str) -> str:
    start = text.index(f"def {name}(")
    end = text.find("\ndef ", start + 10)
    return text[start:] if end == -1 else text[start:end]


def test_lbg_control_changes_are_autosaved_and_notified():
    text = _source(WEEKLY)
    callback = _function(text, "_autosave_lbg_filter_context")
    assert "_LBG_CONTEXT_SNAPSHOT_KEY" in callback
    assert "_LBG_NOTICE_KEY" in callback
    for label in ("Nguồn dữ liệu", "Năm học", "Tuần", "Lớp / Môn dạy", "PPCT"):
        assert f'args=("{label}",' in text


def test_week_sync_is_bidirectional_without_overriding_direct_user_choice():
    text = _source(WEEKLY)
    reverse = _function(text, "_sync_lbg_week_from_loaded_data")
    assert "_ACTIVE_VIEW_KEY" in reverse
    assert 'st.session_state["system_weekly_week_number"] = data_week' in reverse
    assert 'st.session_state["lbg_user_week_number"] = data_week' in reverse
    assert "_STANDARDIZATION_WEEK_KEY" in reverse
    assert "_LBG_WEEK_USER_CHANGE_KEY" in reverse


def test_lbg_controls_use_modern_contrast_3d_style():
    text = _source(WEEKLY)
    assert "linear-gradient(145deg,#0b2749,#06172c)" in text
    assert "box-shadow:4px 5px 0 #03101f" in text
    assert "font-size:14px !important" in text


def test_ai_editor_autosaves_and_uses_floating_notifications():
    text = _source(AI)
    callback = _function(text, "_autosave_ai_document")
    assert "SAVED_KEY" in callback
    assert "AI_AUTOSAVE_NOTICE_KEY" in callback
    assert "on_change=_autosave_ai_document" in text
    assert 'st.toast(str(autosave_notice), icon="💾")' in text
