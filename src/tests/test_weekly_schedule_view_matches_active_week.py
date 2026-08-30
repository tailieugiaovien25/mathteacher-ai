
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


def consistency_block():
    text = technical_workspace()

    start = text.index(
        "# ACTIVE_WEEK_VIEW_CONSISTENCY_V1"
    )

    end = text.index(
        'key="system_weekly_generate"',
        start,
    )

    return text[start:end]


def test_cached_view_must_match_selected_week():
    text = consistency_block()

    assert "_cached_year" in text
    assert "_cached_week" in text

    assert (
        "_cached_week != int(week_number)"
        in text
    )


def test_exact_schedule_id_is_used():
    text = consistency_block()

    assert '"SYSTEM-"' in text
    assert "+ str(academic_year)" in text
    assert "+ str(week_number)" in text


def test_mismatched_view_loads_from_repository():
    text = consistency_block()

    assert (
        "_active_repository.get("
        in text
    )

    assert (
        "_active_schedule_id"
        in text
    )


def test_consistency_restore_is_read_only():
    text = consistency_block()

    assert ".save(" not in text
    assert "runtime.generate(" not in text


def test_stale_view_is_removed_when_week_not_saved():
    text = consistency_block()

    assert (
        "st.session_state.pop("
        in text
    )

    assert (
        "_VIEW_STATE_KEY"
        in text
    )


def test_exact_week_republishes_global_context():
    text = consistency_block()
    assert "_ACTIVE_SCHEDULE_ID_KEY" in text
    assert "_ACTIVE_VIEW_KEY" in text
    assert "week_number is the UI/global source of truth" in text
    assert "_ACTIVE_ACADEMIC_YEAR_KEY" not in text


def test_existing_update_save_pipeline_preserved():
    text = technical_workspace()

    assert (
        "schedule_repository.save("
        in text
    )

    assert (
        "schedule_repository.get("
        in text
    )


def test_persistent_restore_preserved():
    text = technical_workspace()

    assert (
        "GLOBAL_WEEKLY_CONTEXT_PERSISTENT_RESTORE_V1"
        in text
    )


def test_no_schema_change():
    text = source().lower()

    for token in (
        "create table",
        "alter table",
        "drop table",
    ):
        assert token not in text
