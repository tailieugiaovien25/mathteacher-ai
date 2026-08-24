
from pathlib import Path


UI = Path(
    "src/portal_v2/ui/weekly_schedule_streamlit.py"
)


def source():
    return UI.read_text(
        encoding="utf-8"
    )


def technical_workspace():
    text = source()

    start = text.index(
        "def _render_weekly_schedule_technical_workspace("
    )

    end = text.find(
        "\ndef ",
        start + 10,
    )

    if end == -1:
        end = len(text)

    return text[start:end]


def restore_segment():
    text = technical_workspace()

    start = text.index(
        "# GLOBAL_WEEKLY_CONTEXT_PERSISTENT_RESTORE_V1"
    )

    selector = text.index(
        'key="system_weekly_week_number"',
        start,
    )

    return text[start:selector]


def test_new_session_reads_saved_schedules():
    text = restore_segment()

    assert ".list_for_teacher(" in text
    assert "_saved_schedule_summaries" in text


def test_restore_selects_most_recent_update():
    text = restore_segment()

    assert "_latest_summary = max(" in text
    assert '"updated_at"' in text


def test_restore_is_for_current_academic_year():
    text = restore_segment()

    assert "_current_year_summaries" in text
    assert "== str(academic_year)" in text


def test_persisted_schedule_is_read_not_regenerated():
    text = restore_segment()

    assert "_bootstrap_repository.get(" in text
    assert ".save(" not in text
    assert "runtime.generate(" not in text


def test_restored_week_is_published_globally():
    text = restore_segment()

    assert "_ACTIVE_SCHEDULE_ID_KEY" in text
    assert "_ACTIVE_ACADEMIC_YEAR_KEY" in text
    assert "_ACTIVE_WEEK_NUMBER_KEY" in text
    assert "_ACTIVE_VIEW_KEY" in text


def test_widget_receives_restored_week_before_creation():
    text = technical_workspace()

    marker = text.index(
        "# GLOBAL_WEEKLY_CONTEXT_PERSISTENT_RESTORE_V1"
    )

    state_key = text.index(
        '"system_weekly_week_number"',
        marker,
    )

    bootstrap_value = text.index(
        "_bootstrap_week",
        state_key,
    )

    selector = text.index(
        'key="system_weekly_week_number"',
        bootstrap_value,
    )

    assert (
        marker
        < state_key
        < bootstrap_value
        < selector
    )


def test_existing_save_pipeline_remains():
    text = technical_workspace()

    assert "schedule_repository.save(" in text
    assert "schedule_repository.get(" in text


def test_global_context_wiring_remains():
    text = source()

    assert "global_weekly_active_schedule_id" in text
    assert "global_weekly_active_academic_year" in text
    assert "global_weekly_active_week_number" in text
    assert "global_weekly_active_view" in text


def test_no_schema_mutation():
    text = source().lower()

    for token in (
        "create table",
        "alter table",
        "drop table",
    ):
        assert token not in text
