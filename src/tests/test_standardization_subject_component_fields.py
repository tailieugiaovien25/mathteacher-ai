from pathlib import Path


UI = Path(
    "src/portal_v2/ui/weekly_schedule_streamlit.py"
)


def source() -> str:
    return UI.read_text(encoding="utf-8-sig")


def test_subject_and_component_are_resolved_independently():
    text = source()

    assert "def _subject_component_display_names(" in text
    assert "subject_name or subject_value or" in text
    assert "component_name or component_value or" in text
    assert "context_subject," in text
    assert "context_component," in text


def test_context_cards_show_two_separate_fields():
    text = source()

    assert '<div class="mt-context-label">MÔN</div>' in text
    assert '<div class="mt-context-label">PHÂN MÔN</div>' in text
    assert "{escape(context_subject)}" in text
    assert "{escape(context_component)}" in text
    assert '<div class="mt-context-label">MÔN / PHÂN MÔN</div>' not in text


def test_selected_lesson_carries_both_display_names():
    text = source()

    assert '"subject_name": context_subject' in text
    assert '"component_name": context_component' in text
