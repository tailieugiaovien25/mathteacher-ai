from pathlib import Path


WEEKLY_UI = Path("src/portal_v2/ui/weekly_schedule_streamlit.py")
AI_UI = Path("src/portal_v2/ui/lesson_authoring_ai_streamlit.py")


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _function(text: str, name: str) -> str:
    start = text.index(f"def {name}(")
    end = text.find("\ndef ", start + 10)
    return text[start:] if end == -1 else text[start:end]


def test_open_ai_saves_complete_read_only_working_snapshot_and_notice():
    function = _function(_source(WEEKLY_UI), "_open_ai_authoring_page")
    assert "_WORKING_LESSON_CONTEXT_KEY" in function
    assert "dict(transferred_context)" in function
    assert "_LESSON_AUTHORING_NOTICE_KEY" in function


def test_return_to_standardization_restores_source_snapshot_not_ai_metadata():
    function = _function(_source(AI_UI), "_open_standardization")
    assert "WORKING_CONTEXT_KEY" in function
    assert "RESTORE_CONTEXT_KEY" in function
    assert "NAVIGATION_NOTICE_KEY" in function
    transfer = _function(_source(AI_UI), "_publish_standardization_transfer")
    for field in ("week_number", "subject_ref", "curriculum_period", "teaching_date"):
        assert f'"{field}":' not in transfer


def test_multivalue_fields_and_summary_cards_do_not_truncate():
    weekly = _source(WEEKLY_UI)
    ai = _source(AI_UI)
    assert 'text_input(\n        "Lớp dạy"' in weekly
    assert 'text_input(\n        "Ngày dạy"' in weekly
    assert 'teaching_date_display_value = "; ".join(' in weekly
    assert "text-overflow:clip" in ai
    assert "white-space:normal" in ai
    assert "overflow-wrap:anywhere" in ai


def test_catalog_keeps_complete_multiclass_context_with_current_draft():
    function = _function(_source(AI_UI), "_save_to_management_catalog")
    for field in (
        "linked_lesson_context",
        "classes",
        "periods",
        "teaching_dates_by_class",
        "timetable_periods_by_class",
    ):
        assert f'"{field}"' in function
