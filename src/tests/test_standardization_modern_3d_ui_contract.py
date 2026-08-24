
from pathlib import Path


UI = Path(
    "src/portal_v2/ui/weekly_schedule_streamlit.py"
)


def source():
    return UI.read_text(
        encoding="utf-8"
    )


def test_modern_3d_ui_exists():

    text = source()

    assert (
        "STANDARDIZATION_MODERN_3D_UI_V1"
        in text
    )

    assert (
        "def _render_standardization_modern_3d_header("
        in text
    )


def test_3d_ui_component_remains_available_without_hiding_full_ui():

    text = source()

    assert "standardization_minimal_ui = False" in text
    assert "def _render_standardization_modern_3d_header(" in text


def test_full_ui_v1_is_enabled():

    text = source()

    assert (
        "STANDARDIZATION_FULL_UI_V1"
        in text
    )


def test_lbg_bridge_is_preserved():

    text = source()

    assert (
        "_render_lbg_table("
        in text
    )

    assert (
        "_VIEW_STATE_KEY"
        in text
    )


def test_ai_transfer_is_preserved():

    text = source()

    assert (
        "_latest_ai_standardization_transfer()"
        in text
    )

    assert (
        '"docx_bytes"'
        in text
    )


def test_original_document_is_preserved():

    text = source()

    assert (
        '"source_bytes"'
        in text
    )


def test_control_panel_is_preserved():

    text = source()

    assert (
        "def _render_standardization_control_panel("
        in text
    )

    assert (
        "standardization_control_panel_confirm"
        in text
    )


def test_control_panel_is_collapsed_by_default():

    text = source()

    start = text.index(
        "def _render_standardization_control_panel() -> None:"
    )

    segment = text[
        start:
        start + 2500
    ]

    assert (
        "expanded=False"
        in segment
    )


def test_confirmed_date_features_remain():

    text = source()

    assert (
        "standardization_drafting_before_monday_enabled"
        in text
    )

    assert (
        "standardization_approval_before_monday_enabled"
        in text
    )


def test_image_autofit_remains():

    text = source()

    assert (
        "standardization_image_autofit_enabled"
        in text
    )


def test_active_week_authority_remains():

    text = source()

    assert (
        "_ACTIVE_WEEK_NUMBER_KEY"
        in text
    )


def test_no_database_schema_change():

    text = source().lower()

    for token in (
        "create table",
        "alter table",
        "drop table",
    ):
        assert token not in text
