
from pathlib import Path


UI = Path(
    "src/portal_v2/ui/weekly_schedule_streamlit.py"
)


def source():
    return UI.read_text(
        encoding="utf-8"
    )


def test_global_context_keys_exist():
    text = source()

    assert (
        "global_weekly_active_schedule_id"
        in text
    )

    assert (
        "global_weekly_active_academic_year"
        in text
    )

    assert (
        "global_weekly_active_week_number"
        in text
    )

    assert (
        "global_weekly_active_view"
        in text
    )


def test_active_week_published_after_persistence():
    text = source()

    save = text.index(
        "schedule_repository.save("
    )

    get = text.index(
        "schedule_repository.get(",
        save,
    )

    view = text.index(
        "_VIEW_STATE_KEY",
        get,
    )

    publish = text.index(
        "_ACTIVE_WEEK_NUMBER_KEY",
        view,
    )

    assert (
        save
        < get
        < view
        < publish
    )


def test_ai_and_standardization_share_workspace():
    text = source()

    ai = text.index(
        "def render_lesson_authoring_tools_workspace("
    )

    common = text.index(
        "render_weekly_schedule_workspace(",
        ai,
    )

    workspace = text.index(
        "def render_weekly_schedule_workspace(",
        common,
    )

    assert (
        ai
        < common
        < workspace
    )


def test_common_workspace_consumes_active_week():
    text = source()

    start = text.index(
        "def render_weekly_schedule_workspace("
    )

    workspace = text[start:]

    assert (
        "_ACTIVE_ACADEMIC_YEAR_KEY"
        in workspace
    )

    assert (
        "_ACTIVE_WEEK_NUMBER_KEY"
        in workspace
    )

    assert (
        "_ACTIVE_VIEW_KEY"
        in workspace
    )

    # Global weekly context remains available to
    # So?n b?i AI / Chu?n h?a gi?o ?n, but it must
    # never drive the LBG week selector backwards.
    assert (
        'st.session_state[\n'
        '            "system_weekly_week_number"\n'
        '        ] = int(active_week)'
        not in workspace
    )




def test_standardization_engine_not_modified():
    text = source()

    assert (
        "STANDARDIZATION_DRAFTING_APPROVAL_V2"
        in text
    )

    assert (
        "STANDARDIZATION_ASSIGNMENT_TIMETABLE_SYNC_V1"
        in text
    )

    assert (
        "STANDARDIZATION_IMAGE_AUTOFIT_V1"
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
