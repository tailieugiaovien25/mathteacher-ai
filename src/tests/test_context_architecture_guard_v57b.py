# V57-B PHASE 1
from pathlib import Path

from portal_v2.context.architecture_guard import inspect_migrated_streamlit_file


def test_guard_is_compatibility_first_for_legacy_file(tmp_path: Path) -> None:
    path = tmp_path / "legacy.py"
    path.write_text(
        "import streamlit as st\n"
        "st.selectbox('subject', ['A', 'B'])\n",
        encoding="utf-8",
    )
    assert inspect_migrated_streamlit_file(path) == ()


def test_guard_flags_context_widget_without_key_after_migration(tmp_path: Path) -> None:
    path = tmp_path / "migrated.py"
    path.write_text(
        "import streamlit as st\n"
        "CONTEXT_REGISTRY_MIGRATED = True\n"
        "st.selectbox('subject', ['A', 'B'])\n",
        encoding="utf-8",
    )
    findings = inspect_migrated_streamlit_file(path)
    assert len(findings) == 1
    assert findings[0].code == "CONTEXT_WIDGET_MISSING_EXPLICIT_KEY"


def test_guard_accepts_explicit_key_after_migration(tmp_path: Path) -> None:
    path = tmp_path / "migrated.py"
    path.write_text(
        "import streamlit as st\n"
        "CONTEXT_REGISTRY_MIGRATED = True\n"
        "st.selectbox('subject', ['A', 'B'], key='subject_ref')\n",
        encoding="utf-8",
    )
    assert inspect_migrated_streamlit_file(path) == ()
