
from pathlib import Path


UI = Path(
    "src/portal_v2/ui/weekly_schedule_streamlit.py"
)


def source():
    return UI.read_text(
        encoding="utf-8"
    )


def workspace():
    text = source()

    start = text.index(
        "def render_weekly_schedule_workspace("
    )

    end = text.find(
        "\ndef ",
        start + 10,
    )

    if end == -1:
        end = len(text)

    return text[start:end]


def test_standardization_restores_full_ui_mode():
    text = workspace()

    assert (
        "STANDARDIZATION_FULL_UI_V1"
        in text
    )

    assert (
        "standardization_minimal_ui = False"
        in text
    )


def test_standardization_hides_legacy_entry_hub_but_preserves_other_page_path():
    text = workspace()

    assert (
        "_render_lesson_authoring_tool_hub("
        in text
    )

    assert "show_entry_actions=True" in text
    assert 'if page_title == "Chuẩn hóa giáo án":' in text
    assert "omit the legacy entry hub" in text
    assert 'workspace_focus = "STANDARDIZE"' in text


def test_standardization_does_not_force_compact_inner_workspace():
    text = workspace()

    assert "compact_setup_ui=compact_hidden" in text
    assert "if standardization_minimal_ui\n" not in text


def test_week_context_ui_is_hidden_and_data_bridge_is_preserved():
    text = workspace()

    assert (
        'page_title == "Chuẩn hóa giáo án"'
        in text
    )

    # Data resolution remains.
    assert (
        "week_numbers"
        in text
    )

    assert (
        "_ACTIVE_WEEK_NUMBER_KEY"
        in text
    )


def test_lbg_bridge_is_preserved():
    text = workspace()

    assert (
        "_render_lbg_table("
        in text
    )

    assert "_render_lesson_plan_standardization_workspace(" in text

    assert (
        "workspace_focus=workspace_focus"
        in text
    )


def test_standardization_control_panel_is_preserved():
    text = source()

    assert (
        "def _render_standardization_control_panel("
        in text
    )

    assert (
        "standardization_control_panel_confirm"
        in text
    )


def test_ai_transfer_is_preserved():
    text = source()

    assert (
        "_latest_ai_standardization_transfer()"
        in text
    )

    assert '"docx_bytes"' in text
    assert '"source_bytes"' in text


def test_one_way_week_flow_is_preserved():
    text = source()

    assert (
        "WEEK_SELECTOR_ONE_WAY_V2"
        in text
    )


def test_active_week_authority_is_preserved():
    text = source()
    assert "V57-F2C5G_CANONICAL_WEEK_AUTHORITY" in text
    assert "SystemContext.week_number is the only business-context authority" in text


def test_no_schema_change():
    text = source().lower()

    for token in (
        "create table",
        "alter table",
        "drop table",
    ):
        assert token not in text
