"""Standalone Streamlit entry point for the credential-free Math 6 MVP."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))


def main() -> None:
    import streamlit as st

    from portal_v2.ui.math6_mvp_demo_streamlit import (
        render_math6_mvp_demo,
    )

    st.set_page_config(
        page_title="MVP tạo đề Toán 6",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    render_math6_mvp_demo(st)


if __name__ == "__main__":
    main()
