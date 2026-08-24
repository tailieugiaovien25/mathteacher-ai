from pathlib import Path


TIMETABLE = Path("src/portal_v2/ui/teacher_timetable_streamlit.py")
APP = Path("scripts/teacher_portal/app.py")


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _function(text: str, name: str) -> str:
    start = text.index(f"def {name}(")
    end = text.find("\ndef ", start + 10)
    return text[start:] if end == -1 else text[start:end]


def test_page_navigation_autosaves_all_working_contexts_and_notifies():
    text = _source(APP)
    callback = _function(text, "_autosave_before_portal_navigation")
    assert "lesson_authoring_working_context" in callback
    assert "teacher_timetable_autosaved_draft" in callback
    assert "lbg_autosaved_filter_context" in callback
    assert "portal_navigation_notice" in callback
    assert "on_change=_autosave_before_portal_navigation" in text
    assert "st.toast(str(navigation_notice)" in text


def test_timetable_changes_autosave_and_show_floating_notice():
    text = _source(TIMETABLE)
    callback = _function(text, "_autosave_timetable_change")
    assert "_TIMETABLE_DRAFT_KEY" in callback
    assert "_TIMETABLE_NOTICE_KEY" in callback
    assert "on_change=_autosave_timetable_change" in text
    assert 'st.toast(str(floating_notice), icon="💾")' in text


def test_timetable_compacts_top_space_and_uses_modern_3d_cards():
    text = _source(TIMETABLE)
    assert '[data-testid="stHeader"] {height:2.6rem' in text
    assert "padding-top:.35rem" in text
    assert "box-shadow:4px 5px 0 #b8c9dc" in text
    assert "box-shadow:4px 5px 0 #c4d2e3" in text
    assert "font-size:14px!important" in text


def test_empty_or_stale_catalog_falls_back_to_active_assignments():
    text = _source(TIMETABLE)
    assert "or not any(tuple(catalog_snapshot[0] or ()))" in text
    assert "if not subject_scopes:" in text
    fallback = text.index("subject_scopes = tuple(", text.index("if not subject_scopes:"))
    old_return = text.find("\n        return", text.index("if not subject_scopes:"), fallback)
    assert old_return == -1
    assert "for assignment in assignments" in text[fallback:fallback + 1600]
