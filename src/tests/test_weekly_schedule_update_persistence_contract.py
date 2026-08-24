
from pathlib import Path


UI = Path(
    "src/portal_v2/ui/weekly_schedule_streamlit.py"
)


def source():
    return UI.read_text(
        encoding="utf-8"
    )


def update_workspace_source():
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


def test_update_uses_existing_supabase_schedule_repository():
    text = source()

    assert (
        "SupabaseWeeklyScheduleRepository"
        in text
    )


def test_update_persists_generated_schedule():
    text = update_workspace_source()

    generate_pos = text.index(
        "schedule = runtime.generate("
    )

    save_pos = text.index(
        "schedule_repository.save(",
        generate_pos,
    )

    get_pos = text.index(
        "schedule_repository.get(",
        save_pos,
    )

    generation_pos = text.index(
        "generation = (",
        get_pos,
    )

    assert (
        generate_pos
        < save_pos
        < get_pos
        < generation_pos
    )


def test_update_uses_read_after_write_schedule():
    text = update_workspace_source()

    assert (
        "persisted_schedule = ("
        in text
    )

    assert (
        "if persisted_schedule is None:"
        in text
    )

    assert (
        "schedule = persisted_schedule"
        in text
    )


def test_update_keeps_existing_schedule_id_contract():
    text = update_workspace_source()

    assert (
        '"SYSTEM-"'
        in text
    )

    assert (
        "+ academic_year"
        in text
    )

    assert (
        '+ "-W"'
        in text
    )

    assert (
        "+ str(week_number)"
        in text
    )


def test_no_new_storage_schema_is_declared_in_ui():
    text = update_workspace_source()

    forbidden = (
        "create table",
        "alter table",
        "drop table",
        "CREATE TABLE",
        "ALTER TABLE",
        "DROP TABLE",
    )

    assert not any(
        token in text
        for token in forbidden
    )
