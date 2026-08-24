from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEEKLY_UI = (
    ROOT / "src" / "portal_v2" / "ui" / "weekly_schedule_streamlit.py"
)
AI_UI = (
    ROOT / "src" / "portal_v2" / "ui" / "lesson_authoring_ai_streamlit.py"
)


def test_control_panel_requires_explicit_confirmation():
    text = WEEKLY_UI.read_text(encoding="utf-8-sig")

    assert "def _render_standardization_control_panel(" in text
    assert "expanded=False" in text
    assert 'key="standardization_control_panel_confirm"' in text
    assert "lesson_plan_standardization_execute_requested" in text
    assert "process_clicked = bool(" in text
    assert 'lbg_lesson_plan_process_' not in text


def test_control_panel_exposes_all_selective_operations():
    text = WEEKLY_UI.read_text(encoding="utf-8-sig")

    for name in (
        "preserve_original_maximum",
        "sync_context",
        "normalize_font",
        "normalize_equations",
        "normalize_tables",
        "normalize_page_layout",
        "normalize_spacing",
        "normalize_header_footer",
    ):
        assert name in text

    assert "standardization_select_all" in text
    assert "standardization_clear_all" in text


def test_ai_transfer_carries_the_original_word_bytes():
    ai_text = AI_UI.read_text(encoding="utf-8-sig")
    weekly_text = WEEKLY_UI.read_text(encoding="utf-8-sig")

    assert '"source_bytes": item.get("source_bytes")' in ai_text
    assert 'transfer_payload.get("source_bytes")' in weekly_text
    assert '"source_bytes": selected.get("source_bytes")' in weekly_text


def test_confirmed_options_reach_the_processing_service():
    text = WEEKLY_UI.read_text(encoding="utf-8-sig")

    assert "options=confirmed_options" in text
    assert "original_content=original_source_content" in text
    assert "ai_revised_text=ai_revised_text" in text
