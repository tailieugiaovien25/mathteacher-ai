from pathlib import Path


PATH = Path(
    "src/portal_v2/ui/"
    "lesson_plan_template_setup_streamlit.py"
)


def source():
    return PATH.read_text(
        encoding="utf-8-sig"
    )


def test_template_setup_module_exists():
    assert PATH.exists()


def test_template_setup_is_streamlit_ui():
    text = source()

    assert (
        "import streamlit as st"
        in text
    )


def test_template_setup_preserves_template_state():
    text = source()

    assert (
        "session_state"
        in text
    )


def test_template_setup_preserves_rerun_flow():
    text = source()

    assert (
        "st.rerun()"
        in text
    )


def test_template_setup_has_template_editing_boundary():
    text = source()

    assert (
        "_clear_template_widget_state"
        in text
    )


def test_template_setup_does_not_embed_fixed_demo_lesson():
    text = source()

    assert (
        "TI?T 10 + 11"
        not in text
    )

    assert (
        "Ng?y 26 th?ng 10 n?m 2026"
        not in text
    )
