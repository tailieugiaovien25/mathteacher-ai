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
    height: 1px;
    min-height: 1px;
    margin-top: 1rem;
    margin-bottom: 1rem;
    padding: 0;
    border: 0;
    border-radius: 0;
    background: #e6eaf2;
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


def _lesson_authoring_design_system_css() -> str:
    """Visual system for the teacher lesson-authoring workspace."""
    return """
<style>

/* ==========================================================
   MathTeacher AI - Lesson Authoring Workspace
   ========================================================== */

.mt-authoring-shell {
    margin-top: 0.35rem;
    margin-bottom: 1.25rem;
}

/* ==========================================================
   Lesson authoring tool hub
   ========================================================== */

.mt-tool-hub {
    margin: 0.15rem 0 1.15rem;
    font-family:
        Inter, ui-sans-serif, system-ui, -apple-system,
        BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.mt-tool-hub-heading {
    margin: 0;
    font-size: clamp(1.75rem, 3vw, 2.35rem);
    line-height: 1.15;
    font-weight: 780;
    letter-spacing: -0.035em;
    color: #111d4a;
}

.mt-tool-hub-lead {
    max-width: 760px;
    margin: 0.48rem 0 1.15rem;
    font-size: 0.96rem;
    line-height: 1.6;
    color: #667085;
}

.mt-tool-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
}

.mt-tool-card {
    position: relative;
    overflow: hidden;
    min-height: 230px;
    padding: 1.3rem 1.35rem 1.2rem;
    border: 1px solid #e3e9f5;
    border-radius: 20px;
    background: #ffffff;
    box-shadow: 0 10px 28px rgba(30, 53, 110, 0.07);
}

.mt-tool-card::before {
    position: absolute;
    top: 0;
    right: 0;
    left: 0;
    height: 6px;
    content: "";
}

.mt-tool-card-ai::before {
    background: linear-gradient(90deg, #3767f4, #5b46f5);
}

.mt-tool-card-standard::before {
    background: linear-gradient(90deg, #0796a5, #10b9a6);
}

.mt-tool-card-ai.is-active {
    border-color: rgba(55, 103, 244, 0.42);
    box-shadow: 0 14px 34px rgba(49, 88, 231, 0.14);
}

.mt-tool-card-standard.is-active {
    border-color: rgba(7, 150, 165, 0.42);
    box-shadow: 0 14px 34px rgba(8, 127, 140, 0.14);
}

.mt-tool-card-body {
    display: grid;
    grid-template-columns: 64px minmax(0, 1fr);
    gap: 1rem;
    align-items: start;
}

.mt-tool-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    border-radius: 18px;
    font-size: 1.8rem;
    line-height: 1;
}

.mt-tool-card-ai .mt-tool-icon {
    color: #3158e7;
    background: linear-gradient(145deg, #edf2ff, #e4e9ff);
}

.mt-tool-card-standard .mt-tool-icon {
    color: #087f8c;
    background: linear-gradient(145deg, #e8fbfa, #dcf7f3);
}

.mt-tool-kicker {
    margin-bottom: 0.28rem;
    font-size: 0.72rem;
    line-height: 1.2;
    font-weight: 750;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.mt-tool-card-ai .mt-tool-kicker,
.mt-tool-card-ai .mt-tool-title {
    color: #3158e7;
}

.mt-tool-card-standard .mt-tool-kicker,
.mt-tool-card-standard .mt-tool-title {
    color: #087f8c;
}

.mt-tool-title {
    margin: 0;
    font-size: clamp(1.1rem, 2vw, 1.42rem);
    line-height: 1.25;
    font-weight: 800;
    letter-spacing: -0.018em;
}

.mt-tool-description {
    margin-top: 0.58rem;
    font-size: 0.91rem;
    line-height: 1.55;
    color: #667085;
}

.mt-tool-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-top: 1.05rem;
}

.mt-tool-tag {
    display: inline-flex;
    align-items: center;
    min-height: 30px;
    padding: 0.3rem 0.65rem;
    border: 1px solid #e4e9f2;
    border-radius: 999px;
    background: #f8fafc;
    font-size: 0.78rem;
    line-height: 1.2;
    font-weight: 650;
    color: #475467;
}

/* ==========================================================
   AI drafting workspace
   ========================================================== */

.mt-ai-workspace-heading {
    display: grid;
    grid-template-columns: 60px minmax(0, 1fr);
    gap: 1rem;
    align-items: center;
    margin: 1.15rem 0 0.9rem;
    padding: 1rem 1.1rem;
    border: 1px solid #e5eafb;
    border-radius: 18px;
    background: linear-gradient(135deg, #f5f7ff, #ffffff);
}

.mt-ai-workspace-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 60px;
    height: 60px;
    border-radius: 17px;
    background: linear-gradient(145deg, #416cf4, #5948ee);
    box-shadow: 0 10px 22px rgba(65, 88, 210, 0.2);
    font-family: Inter, ui-sans-serif, system-ui, sans-serif;
    font-size: 1.2rem;
    font-weight: 800;
    color: #ffffff;
}

.mt-ai-workspace-title {
    margin: 0;
    font-family: Inter, ui-sans-serif, system-ui, sans-serif;
    font-size: 1.3rem;
    line-height: 1.25;
    font-weight: 800;
    color: #263fbd;
}

.mt-ai-workspace-description {
    margin: 0.3rem 0 0;
    font-family: Inter, ui-sans-serif, system-ui, sans-serif;
    font-size: 0.88rem;
    line-height: 1.5;
    color: #667085;
}

.mt-authoring-hero {
    position: relative;
    overflow: hidden;
    padding: 1.55rem 1.7rem;
    margin: 0.25rem 0 1.15rem 0;

    border: 1px solid rgba(49, 86, 211, 0.14);
    border-radius: 20px;

    background:
        radial-gradient(
            circle at 88% 10%,
            rgba(79, 111, 255, 0.16),
            transparent 32%
        ),
        linear-gradient(
            135deg,
            rgba(246, 249, 255, 0.98),
            rgba(255, 255, 255, 0.98)
        );

    box-shadow:
        0 10px 34px rgba(34, 54, 105, 0.07);
}

.mt-authoring-eyebrow {
    margin-bottom: 0.45rem;

    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;

    color: #4964c6;
}

.mt-authoring-title {
    margin: 0;

    font-size: clamp(1.65rem, 2.5vw, 2.2rem);
    line-height: 1.16;
    font-weight: 760;
    letter-spacing: -0.025em;

    color: #17213c;
}

.mt-authoring-subtitle {
    max-width: 780px;
    margin-top: 0.55rem;

    font-size: 0.96rem;
    line-height: 1.62;

    color: #667085;
}


/* ==========================================================
   Lesson context bar
   ========================================================== */

.mt-lesson-context {
    display: grid;
    grid-template-columns:
        repeat(6, minmax(0, 1fr));

    gap: 0.7rem;

    margin: 0.2rem 0 1.05rem 0;
}

.mt-context-item {
    min-width: 0;
    padding: 0.78rem 0.9rem;

    border: 1px solid #e8ebf2;
    border-radius: 14px;

    background: #ffffff;
}

.mt-context-label {
    margin-bottom: 0.2rem;

    font-size: 0.72rem;
    font-weight: 650;
    letter-spacing: 0.035em;
    text-transform: uppercase;

    color: #98a2b3;
}

.mt-context-value {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;

    font-size: 0.92rem;
    font-weight: 650;

    color: #27324a;
}

.mt-context-item--multiline {
    align-self: stretch;
}

.mt-context-item--multiline .mt-context-value {
    overflow: visible;
    text-overflow: clip;
    white-space: normal;
    overflow-wrap: anywhere;
    line-height: 1.45;
}


/* ==========================================================
   Workflow stepper
   ========================================================== */

.mt-authoring-stepper {
    display: grid;
    grid-template-columns:
        repeat(5, minmax(0, 1fr));

    gap: 0.55rem;

    margin: 0.35rem 0 1.25rem 0;
}

.mt-authoring-step {
    position: relative;

    min-height: 76px;
    padding: 0.72rem 0.72rem 0.7rem;

    border: 1px solid #e6eaf2;
    border-radius: 14px;

    background: #ffffff;
}

.mt-authoring-step.is-active {
    border-color: rgba(65, 91, 210, 0.35);

    background:
        linear-gradient(
            145deg,
            rgba(242, 246, 255, 1),
            rgba(255, 255, 255, 1)
        );

    box-shadow:
        0 6px 18px rgba(50, 74, 170, 0.08);
}

.mt-step-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;

    width: 25px;
    height: 25px;

    margin-bottom: 0.35rem;

    border-radius: 999px;

    background: #eef2ff;

    font-size: 0.76rem;
    font-weight: 750;

    color: #4058b8;
}

.mt-authoring-step.is-active
.mt-step-number {
    background: #4058b8;
    color: #ffffff;
}

.mt-step-title {
    font-size: 0.79rem;
    line-height: 1.3;
    font-weight: 650;

    color: #475467;
}


/* ==========================================================
   Workspace cards
   ========================================================== */

.mt-workspace-card {
    padding: 1rem 1.05rem;

    margin: 0.65rem 0 0.9rem;

    border: 1px solid #e8ebf2;
    border-radius: 16px;

    background: #ffffff;

    box-shadow:
        0 3px 14px rgba(27, 39, 78, 0.035);
}

.mt-synced-lesson-title {
    display: flex;
    align-items: baseline;
    gap: 0.65rem;
    margin: 0.7rem 0 0.55rem;
    padding: 0.72rem 0.9rem;
    border-left: 4px solid #4964e8;
    border-radius: 0 12px 12px 0;
    background: #f6f8ff;
    font-family: Inter, ui-sans-serif, system-ui, sans-serif;
}

.mt-synced-lesson-title span {
    flex: 0 0 auto;
    font-size: 0.7rem;
    font-weight: 750;
    letter-spacing: 0.06em;
    color: #6677ca;
}

.mt-synced-lesson-title strong {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 0.98rem;
    color: #26324b;
}

/* Replaced by the compact lesson-context row in the V3 page. */
.mt-workspace-card,
.mt-authoring-stepper {
    display: none;
}

.mt-workspace-card-title {
    margin-bottom: 0.2rem;

    font-size: 1rem;
    font-weight: 700;

    color: #202b46;
}

.mt-workspace-card-description {
    font-size: 0.86rem;
    line-height: 1.5;

    color: #7a8497;
}


/* ==========================================================
   Section heading
   ========================================================== */

.mt-section-heading {
    margin-top: 1.15rem;
    margin-bottom: 0.7rem;
}

.mt-section-kicker {
    margin-bottom: 0.16rem;

    font-size: 0.73rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;

    color: #6073c7;
}

.mt-section-title {
    margin: 0;

    font-size: 1.18rem;
    font-weight: 720;

    color: #202a44;
}

.mt-section-description {
    max-width: 760px;
    margin-top: 0.25rem;

    font-size: 0.86rem;
    line-height: 1.55;

    color: #7a8497;
}


/* ==========================================================
   Streamlit refinement inside authoring workspace
   ========================================================== */

div[data-testid="stFileUploader"] {
    border-radius: 14px;
}

div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stDateInput"] input {
    border-radius: 10px;
}

div[data-testid="stAlert"] {
    border-radius: 12px;
}


/* ==========================================================
   Responsive layout
   ========================================================== */

@media (max-width: 1000px) {

    .mt-tool-grid {
        grid-template-columns: 1fr;
    }

    .mt-lesson-context {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .mt-authoring-stepper {
        grid-template-columns:
            repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 640px) {

    .mt-tool-card {
        min-height: 0;
        padding: 1.15rem;
        border-radius: 16px;
    }

    .mt-tool-card-body {
        grid-template-columns: 52px minmax(0, 1fr);
        gap: 0.8rem;
    }

    .mt-tool-icon {
        width: 52px;
        height: 52px;
        border-radius: 15px;
        font-size: 1.5rem;
    }

    .mt-authoring-hero {
        padding: 1.2rem;
        border-radius: 16px;
    }

    .mt-lesson-context,
    .mt-authoring-stepper {
        grid-template-columns: 1fr;
    }

    .mt-synced-lesson-title {
        display: block;
    }

    .mt-synced-lesson-title strong {
        display: block;
        margin-top: 0.2rem;
        white-space: normal;
    }
}

</style>
"""


def apply_lesson_authoring_workspace_styles() -> None:
    """Apply the visual system for the lesson-authoring workspace."""
    import streamlit as st

    st.markdown(
        _lesson_authoring_design_system_css(),
        unsafe_allow_html=True,
    )
