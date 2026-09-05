from pathlib import Path
import ast
import re


SOURCE = Path(
    "src/portal_v2/ui/"
    "standardized_lesson_plan_authoring_v2_streamlit.py"
)


def _source():
    return SOURCE.read_text(encoding="utf-8")


def test_all_six_report_cards_are_preserved():
    text = _source()

    for number in range(1, 7):
        assert (
            f'g1b_report_card_{number}'
            in text
        )


def test_every_report_card_is_collapsed_by_default():
    text = _source()
    lines = text.splitlines()

    for number in range(1, 7):
        marker = (
            f'with st.container('
            f'key="g1b_report_card_{number}")'
        )

        start = next(
            index
            for index, line in enumerate(lines)
            if marker in line
        )

        block = "\n".join(
            lines[start:start + 18]
        )

        assert "with st.expander(" in block
        assert "expanded=False" in block


def test_failed_canonical_report_no_longer_auto_opens():
    text = _source()

    assert (
        "expanded=(not canonical_pass_100)"
        not in text
    )


def test_standardized_document_is_primary_when_available():
    text = _source()

    assert (
        "V14B6L_STANDARDIZED_DOCUMENT_PRIMARY_VIEW"
        in text
    )

    assert (
        "if standardized_content:"
        in text
    )

    assert (
        "standardized_tab, original_tab = st.tabs("
        in text
    )

    assert (
        "original_tab, standardized_tab = st.tabs("
        in text
    )


def test_document_rendering_is_preserved():
    text = _source()

    assert "content=original_content" in text
    assert "content=standardized_content" in text

    assert (
        text.count(
            "preview_html_builder=preview_html_builder"
        )
        >= 2
    )


def test_standardizer_and_audit_gate_are_unchanged():
    text = _source()

    assert (
        "standardize_handler(**handler_arguments)"
        in text
    )

    assert (
        "st.session_state[STANDARDIZED_DOCUMENT_KEY]"
        in text
    )

    assert "audit_blocks_save" in text


def test_v14b6l_markers_are_unique():
    text = _source()

    assert (
        text.count(
            "V14B6L_COLLAPSED_REPORTS"
        )
        == 1
    )

    assert (
        text.count(
            "V14B6L_STANDARDIZED_DOCUMENT_PRIMARY_VIEW"
        )
        == 1
    )
