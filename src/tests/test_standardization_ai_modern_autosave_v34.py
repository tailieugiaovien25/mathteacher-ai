from pathlib import Path


WEEKLY = Path("src/portal_v2/ui/weekly_schedule_streamlit.py")
AI = Path("src/portal_v2/ui/lesson_authoring_ai_streamlit.py")


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _function(text: str, name: str) -> str:
    start = text.index(f"def {name}(")
    end = text.find("\ndef ", start + 10)
    return text[start:] if end == -1 else text[start:end]


def test_standardization_all_primary_selectors_autosave_and_notify():
    text = _source(WEEKLY)
    callback = _function(text, "_autosave_standardization_change")
    assert "_STANDARDIZATION_DRAFT_KEY" in callback
    assert "_STANDARDIZATION_NOTICE_KEY" in callback
    for label in ("Môn", "Phân môn", "Cách thực hiện"):
        assert f'args=("{label}",' in text
    assert '_autosave_standardization_change("Tiết PPCT / Bài dạy")' in text
    assert 'st.toast(str(standardization_notice), icon="💾")' in text
    assert '"selected_lesson": dict(selected_lesson)' in text


def test_standardization_week_change_autosaves_and_remains_two_way():
    text = _source(WEEKLY)
    callback = _function(text, "_sync_standardization_week_to_lbg")
    assert "_emit_canonical_week_change(" in callback
    assert "source_control=_STANDARDIZATION_WEEK_KEY" in callback
    assert '_autosave_standardization_change("Tuần soạn")' in callback
    assert '"system_weekly_week_number"' not in callback


def test_standardization_controls_and_ai_button_have_contrast_3d_style():
    text = _source(WEEKLY)
    assert "linear-gradient(145deg,#ffffff,#edf5ff)" in text
    assert "2px 3px 0 #c5d3e4" in text
    assert "linear-gradient(145deg,#3789e8,#1f63bd)" in text


def test_ai_context_selectors_and_document_are_autosaved():
    text = _source(AI)
    callback = _function(text, "_notify_ai_context_change")
    assert "AI_CONTEXT_DRAFT_KEY" in callback
    assert "AI_AUTOSAVE_NOTICE_KEY" in callback
    assert 'args=("Môn/phân môn",)' in text
    assert 'args=("Bài từ Lịch báo giảng",)' in text
    assert "on_change=_autosave_ai_document" in text


def test_ai_page_uses_compact_typography_and_rounded_3d_panels():
    text = _source(AI)
    assert "font-size:16px" in text
    assert "font-size:14px" in text
    assert "border-radius:12px" in text
    assert "linear-gradient(145deg,#ffffff,#e8f2ff)" in text
