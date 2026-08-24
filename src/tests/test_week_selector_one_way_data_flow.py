
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


def test_selector_is_week_authority():
    text = technical_workspace()

    assert (
        'key="system_weekly_week_number"'
        in text
    )

    assert (
        "requested_week_number = int("
        in text
    )

    assert (
        "week_number = ("
        in text
    )


def test_selector_has_no_forced_week_one():
    text = technical_workspace()

    pos = text.index(
        'key="system_weekly_week_number"'
    )

    block = text[
        max(0, pos - 350):
        pos + 100
    ]

    assert "index=0" not in block


def test_bootstrap_cannot_write_selector():
    text = source()

    assert (
        '"system_weekly_week_number"\n'
        '                ] = _bootstrap_week'
        not in text
    )


def test_active_week_cannot_write_selector():
    text = source()

    assert (
        '"system_weekly_week_number"\n'
        '        ] = int(active_week)'
        not in text
    )

    assert (
        '"system_weekly_week_number"\n'
        '            ] = int(active_week)'
        not in text
    )


def test_selected_week_still_drives_view():
    text = technical_workspace()

    assert (
        "_cached_week != int(week_number)"
        in text
    )

    assert (
        "+ str(week_number)"
        in text
    )


def test_save_pipeline_preserved():
    text = technical_workspace()

    assert (
        "schedule_repository.save("
        in text
    )

    assert (
        "schedule_repository.get("
        in text
    )


def test_global_publish_after_update_preserved():
    text = technical_workspace()

    assert (
        "_ACTIVE_WEEK_NUMBER_KEY"
        in text
    )

    assert (
        "_ACTIVE_VIEW_KEY"
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
