"""Shared visual styles for teacher-facing Streamlit workspaces."""

from __future__ import annotations

from typing import Any


TEACHER_WORKSPACE_CSS = r"""
<style>

/* ==========================================================
   MathTeacher-AI Teacher Workspace
   Typography contract:
   - Times New Roman
   - 14px base
   - 1.5 line height
   - compact vertical rhythm
   ========================================================== */


/* ----------------------------------------------------------
   Main application text
   ---------------------------------------------------------- */

[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] td,
[data-testid="stAppViewContainer"] th,
[data-testid="stAppViewContainer"] input,
[data-testid="stAppViewContainer"] textarea,
[data-testid="stAppViewContainer"] button {
    font-family: "Times New Roman", Times, serif;
}


/* ----------------------------------------------------------
   Base content
   ---------------------------------------------------------- */

[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] label {
    font-size: 14px;
    line-height: 1.5;
}


/* ----------------------------------------------------------
   Headings
   ---------------------------------------------------------- */

[data-testid="stAppViewContainer"] h1 {
    font-family: "Times New Roman", Times, serif;
    font-size: 26px;
    line-height: 1.5;
    margin-top: 0.15rem;
    margin-bottom: 0.45rem;
}

[data-testid="stAppViewContainer"] h2 {
    font-family: "Times New Roman", Times, serif;
    font-size: 20px;
    line-height: 1.5;
    margin-top: 0.45rem;
    margin-bottom: 0.35rem;
}

[data-testid="stAppViewContainer"] h3 {
    font-family: "Times New Roman", Times, serif;
    font-size: 16px;
    line-height: 1.5;
    margin-top: 0.4rem;
    margin-bottom: 0.3rem;
}


/* ----------------------------------------------------------
   Inputs
   ---------------------------------------------------------- */

[data-testid="stAppViewContainer"] input,
[data-testid="stAppViewContainer"] textarea {
    font-size: 14px;
    line-height: 1.5;
}

[data-testid="stAppViewContainer"] [data-baseweb="select"] {
    font-family: "Times New Roman", Times, serif;
    font-size: 14px;
}


/* ----------------------------------------------------------
   Buttons
   ---------------------------------------------------------- */

[data-testid="stAppViewContainer"] .stButton > button,
[data-testid="stAppViewContainer"] .stDownloadButton > button {
    font-family: "Times New Roman", Times, serif;
    font-size: 14px;
    font-weight: 600;
    line-height: 1.5;

    min-height: 44px;

    padding-top: 0.45rem;
    padding-bottom: 0.45rem;
    padding-left: 0.8rem;
    padding-right: 0.8rem;
}


/* ----------------------------------------------------------
   Captions
   ---------------------------------------------------------- */

[data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] {
    font-family: "Times New Roman", Times, serif;
    font-size: 14px;
    line-height: 1.5;
}


/* ----------------------------------------------------------
   Tables / dataframes
   ---------------------------------------------------------- */

[data-testid="stAppViewContainer"] table {
    font-family: "Times New Roman", Times, serif;
    font-size: 14px;
    line-height: 1.5;
}


/* ----------------------------------------------------------
   Compact vertical rhythm
   ---------------------------------------------------------- */

[data-testid="stAppViewContainer"] p {
    margin-top: 0.15rem;
    margin-bottom: 0.3rem;
}

[data-testid="stAppViewContainer"] hr {
    margin-top: 0.55rem;
    margin-bottom: 0.55rem;
}


/* ----------------------------------------------------------
   Streamlit vertical blocks

   Keep this conservative. We reduce excessive whitespace
   without collapsing widget internals.
   ---------------------------------------------------------- */

[data-testid="stAppViewContainer"]
[data-testid="stVerticalBlock"] {
    gap: 0.55rem;
}


/* ----------------------------------------------------------
   Main page width / top spacing
   ---------------------------------------------------------- */

.block-container {
    max-width: 1240px;
    padding-top: 0.75rem;
    padding-bottom: 1rem;
}


/* ----------------------------------------------------------
   Sidebar

   Typography follows the same teacher workspace contract.
   ---------------------------------------------------------- */

[data-testid="stSidebar"],
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] button {
    font-family: "Times New Roman", Times, serif;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {
    font-size: 14px;
    line-height: 1.5;
}

[data-testid="stSidebar"] {
    border-right: 1px solid #e5e7eb;
}



/* ----------------------------------------------------------
   Major workspace section separator

   Visual contract:
   - full content width
   - light blue
   - 2 cm high
   ---------------------------------------------------------- */

.mt-workspace-section-separator {
    display: block;
    width: 100%;
    height: 2cm;
    min-height: 2cm;
    margin-top: 0.35rem;
    margin-bottom: 0.35rem;
    padding: 0;
    border: 0;
    border-radius: 0;
    background: #e8f2ff;
}

</style>
"""


def apply_teacher_workspace_styles(
    st: Any,
) -> None:
    """Apply the shared teacher workspace visual contract."""

    st.markdown(
        TEACHER_WORKSPACE_CSS,
        unsafe_allow_html=True,
    )
