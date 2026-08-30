from pathlib import Path


WEEKLY_UI = Path(
    "src/portal_v2/ui/weekly_schedule_streamlit.py"
)
AI_UI = Path(
    "src/portal_v2/ui/lesson_authoring_ai_streamlit.py"
)


def _function_source(text: str, name: str) -> str:
    start = text.index(f"def {name}(")
    end = text.find("\ndef ", start + 10)
    return text[start:] if end == -1 else text[start:end]


def test_ai_to_standardization_does_not_write_lbg_selection():
    text = AI_UI.read_text(encoding="utf-8-sig")
    function = _function_source(text, "_open_standardization")

    assert 'st.session_state["lbg_user_academic_year"]' not in function
    assert 'st.session_state["lbg_user_week_number"]' not in function
    assert '"portal_page"' in function
    assert '"lesson_authoring_standardization_document"' in function


def test_management_to_standardization_does_not_write_lbg_selection():
    text = WEEKLY_UI.read_text(encoding="utf-8-sig")
    function = _function_source(text, "_open_management_catalogue_item")
    assert 'st.session_state["lbg_user_academic_year"]' not in function
    assert 'st.session_state["lbg_user_week_number"]' not in function
    assert '"portal_navigation_request"' in function
    assert '"_standardization_transfer"' in function


def test_standardization_never_uses_ai_transfer_as_week_authority():
    text = WEEKLY_UI.read_text(encoding="utf-8-sig")
    function = _function_source(text, "render_weekly_schedule_workspace")
    assert "transferred_week" not in function
    assert "SystemContext.week_number is the only business-context authority" in function
    assert "get_canonical_context(" in function


def test_destination_reads_persisted_lbg_without_regenerating_it():
    text = WEEKLY_UI.read_text(encoding="utf-8-sig")
    function = _function_source(
        text,
        "render_weekly_schedule_workspace",
    )

    assert "SupabaseWeeklyScheduleRepository(" in function
    assert ").get(schedule_id)" in function
    assert "runtime.generate(" not in function
    assert "schedule_repository.save(" not in function


def test_destination_does_not_mutate_source_widget_state():
    text = WEEKLY_UI.read_text(encoding="utf-8-sig")
    function = _function_source(
        text,
        "render_weekly_schedule_workspace",
    )

    assert (
        'st.session_state[\n'
        '            "system_weekly_academic_year"'
        not in function
    )
    assert (
        'st.session_state[\n'
        '            "_system_weekly_last_updated_week"'
        not in function
    )
    assert "st.session_state.pop(\n            _VIEW_STATE_KEY" not in function


def test_lbg_source_update_pipeline_remains_unchanged():
    text = WEEKLY_UI.read_text(encoding="utf-8-sig")
    function = _function_source(
        text,
        "_render_weekly_schedule_technical_workspace",
    )

    assert "schedule = runtime.generate(" in function
    assert "schedule_repository.save(" in function
    assert "persisted_schedule = (" in function
    assert "_ACTIVE_WEEK_NUMBER_KEY" in function
    assert "_ACTIVE_VIEW_KEY" in function

