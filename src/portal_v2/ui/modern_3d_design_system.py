"""Shared modern three-dimensional visual system for MathTeacher-AI."""

from __future__ import annotations

from typing import Any


MODERN_3D_DESIGN_SYSTEM_CSS = r"""
<style>
:root {
    --mt-navy-950: #06162f;
    --mt-navy-900: #09213f;
    --mt-blue-700: #1757b8;
    --mt-blue-600: #236bc6;
    --mt-blue-500: #3485df;
    --mt-cyan-400: #55d7e8;
    --mt-teal-500: #13a99b;
    --mt-surface: rgba(255, 255, 255, 0.92);
    --mt-surface-soft: rgba(247, 250, 255, 0.9);
    --mt-border: rgba(124, 151, 188, 0.24);
    --mt-text: #17263d;
    --mt-muted: #68778d;
    --mt-danger: #c83e50;
    --mt-radius-sm: 12px;
    --mt-radius-md: 18px;
    --mt-radius-lg: 26px;
    --mt-shadow-raised:
        0 18px 38px rgba(22, 51, 91, 0.12),
        0 3px 8px rgba(22, 51, 91, 0.08),
        inset 0 1px 0 rgba(255, 255, 255, 0.9);
    --mt-shadow-control:
        0 8px 18px rgba(25, 58, 101, 0.1),
        inset 0 1px 0 rgba(255, 255, 255, 0.85);
    --mt-shadow-pressed:
        inset 0 3px 8px rgba(18, 46, 82, 0.16),
        0 1px 0 rgba(255, 255, 255, 0.9);
}

html,
body,
[class*="css"] {
    font-family: "Segoe UI", Inter, Arial, sans-serif;
}

[data-testid="stAppViewContainer"] {
    color: var(--mt-text);
    background:
        radial-gradient(circle at 8% 5%, rgba(82, 173, 255, 0.17), transparent 28rem),
        radial-gradient(circle at 92% 0%, rgba(70, 224, 207, 0.13), transparent 25rem),
        linear-gradient(145deg, #f6f9ff 0%, #edf4fb 52%, #f8fbff 100%);
    background-attachment: fixed;
}

[data-testid="stAppViewContainer"]::before {
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    content: "";
    opacity: 0.42;
    background-image:
        linear-gradient(rgba(36, 83, 137, 0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(36, 83, 137, 0.035) 1px, transparent 1px);
    background-size: 32px 32px;
}

[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] td,
[data-testid="stAppViewContainer"] th,
[data-testid="stAppViewContainer"] input,
[data-testid="stAppViewContainer"] textarea,
[data-testid="stAppViewContainer"] button,
[data-testid="stSidebar"] * {
    font-family: "Segoe UI", Inter, Arial, sans-serif !important;
}

.block-container {
    width: min(100%, 1380px);
    max-width: 1380px;
    padding: 1.35rem 2rem 2.5rem;
}

h1, h2, h3,
[data-testid="stHeadingWithActionElements"] {
    color: var(--mt-navy-900);
    letter-spacing: -0.025em;
}

[data-testid="stCaptionContainer"],
.stCaption,
small {
    color: var(--mt-muted) !important;
}

/* Sidebar: deep navigation rail with tactile selections. */
[data-testid="stSidebar"] {
    border-right: 1px solid rgba(124, 183, 224, 0.24) !important;
    background:
        radial-gradient(circle at 20% 0%, rgba(41, 133, 189, 0.25), transparent 16rem),
        linear-gradient(180deg, #071d38 0%, #06162f 100%) !important;
    box-shadow: 16px 0 40px rgba(4, 22, 48, 0.18);
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span {
    color: #eef7ff !important;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] button {
    font-size: 0.93rem !important;
    line-height: 1.42 !important;
}

[data-testid="stSidebar"] h1 {
    font-size: 1.35rem !important;
    letter-spacing: -0.025em;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    min-height: 42px;
    margin: 0.13rem 0;
    padding: 0.48rem 0.62rem;
    border: 1px solid transparent;
    border-radius: 12px;
    transition: transform 160ms ease, background 160ms ease, border-color 160ms ease;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    border-color: rgba(111, 211, 255, 0.24);
    background: rgba(72, 155, 213, 0.14);
    transform: translateX(3px);
}

[data-testid="stSidebar"] [data-testid="stAlert"] {
    border: 1px solid rgba(96, 224, 196, 0.3);
    background: rgba(20, 142, 129, 0.2);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.09);
}

/* Buttons: raised controls with a clear pressed state. */
.stButton > button,
.stDownloadButton > button,
[data-testid="stFormSubmitButton"] > button,
[data-testid="baseButton-secondary"],
[data-testid="baseButton-primary"] {
    min-height: 44px;
    border: 1px solid rgba(111, 143, 182, 0.34) !important;
    border-radius: var(--mt-radius-sm) !important;
    color: #17304f !important;
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(235, 243, 252, 0.98)) !important;
    box-shadow: var(--mt-shadow-control) !important;
    font-weight: 650 !important;
    transition: transform 150ms ease, box-shadow 150ms ease, border-color 150ms ease !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    border-color: rgba(44, 117, 198, 0.58) !important;
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(24, 71, 124, 0.16) !important;
}

.stButton > button:active,
.stDownloadButton > button:active,
[data-testid="stFormSubmitButton"] > button:active {
    transform: translateY(1px);
    box-shadow: var(--mt-shadow-pressed) !important;
}

.stButton > button[kind="primary"],
[data-testid="baseButton-primary"],
[data-testid="stFormSubmitButton"] > button {
    border-color: rgba(42, 113, 194, 0.7) !important;
    color: #ffffff !important;
    background:
        linear-gradient(145deg, var(--mt-blue-500), var(--mt-blue-700)) !important;
    box-shadow:
        0 12px 25px rgba(30, 92, 170, 0.27),
        inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
}

[data-testid="stSidebar"] .stButton > button {
    border-color: rgba(125, 187, 229, 0.3) !important;
    color: #f4faff !important;
    background: linear-gradient(180deg, rgba(27, 73, 116, 0.9), rgba(14, 49, 84, 0.95)) !important;
    box-shadow: 0 8px 18px rgba(1, 12, 29, 0.25), inset 0 1px 0 rgba(255,255,255,0.08) !important;
}

/* Inputs and selectors. */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] > div > div {
    border: 1px solid rgba(119, 150, 188, 0.32) !important;
    border-radius: var(--mt-radius-sm) !important;
    color: var(--mt-text) !important;
    background: linear-gradient(180deg, #ffffff, #f4f8fd) !important;
    box-shadow: inset 0 2px 5px rgba(28, 62, 104, 0.06), 0 5px 12px rgba(29, 63, 106, 0.06) !important;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stDateInput"] input:focus {
    border-color: var(--mt-blue-500) !important;
    box-shadow: 0 0 0 3px rgba(52, 133, 223, 0.16), inset 0 2px 5px rgba(28, 62, 104, 0.05) !important;
}

/* Cards, expanders, forms and upload zones. */
[data-testid="stForm"],
[data-testid="stExpander"],
[data-testid="stMetric"],
[data-testid="stFileUploaderDropzone"],
[data-testid="stDataFrame"],
[data-testid="stTable"] {
    border: 1px solid var(--mt-border) !important;
    border-radius: var(--mt-radius-md) !important;
    background: var(--mt-surface) !important;
    box-shadow: var(--mt-shadow-raised) !important;
}

[data-testid="stForm"] {
    padding: 1.25rem !important;
}

[data-testid="stExpander"] {
    overflow: hidden;
}

[data-testid="stExpander"] details > summary {
    min-height: 46px;
    padding: 0.65rem 0.9rem;
    font-weight: 650;
    background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(239,246,253,0.94));
}

[data-testid="stFileUploaderDropzone"] {
    border-style: dashed !important;
    border-width: 1.5px !important;
    background:
        radial-gradient(circle at 50% 0%, rgba(77, 180, 229, 0.11), transparent 70%),
        linear-gradient(180deg, rgba(255,255,255,0.96), rgba(240,247,253,0.96)) !important;
}

[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 0.38rem;
    padding: 0.34rem;
    border: 1px solid var(--mt-border);
    border-radius: 14px;
    background: rgba(231, 240, 250, 0.82);
    box-shadow: inset 0 2px 5px rgba(22, 51, 91, 0.07);
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 10px;
}

[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--mt-blue-700) !important;
    background: #ffffff;
    box-shadow: 0 5px 12px rgba(28, 72, 124, 0.12);
}

[data-testid="stAlert"] {
    border: 1px solid rgba(104, 145, 186, 0.24);
    border-radius: 14px;
    box-shadow: 0 7px 18px rgba(22, 51, 91, 0.08), inset 0 1px 0 rgba(255,255,255,0.7);
}

table {
    overflow: hidden;
    border-collapse: separate !important;
    border-spacing: 0 !important;
    border: 1px solid var(--mt-border);
    border-radius: 14px;
    background: rgba(255,255,255,0.94);
    box-shadow: 0 9px 22px rgba(22, 51, 91, 0.09);
}

table thead th {
    color: #ffffff !important;
    background: linear-gradient(180deg, #123e6e, #09284d) !important;
}

table tbody tr:nth-child(even) {
    background: rgba(236, 244, 252, 0.72);
}

/* Existing custom components receive the same depth language. */
.mt-workspace-card,
.mt-tool-card,
.mt-authoring-hero,
.mt-ai-workspace-heading,
.mt-lesson-context > *,
.mt-synced-lesson-title {
    border-color: var(--mt-border) !important;
    box-shadow: var(--mt-shadow-raised) !important;
}

.mt-workspace-section-separator {
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(55, 118, 183, 0.35), transparent) !important;
}

/* Login scene. */
.mt-login-scene {
    position: relative;
    overflow: hidden;
    max-width: 760px;
    margin: 4vh auto 1rem;
    padding: 2.1rem 2.2rem 1.9rem;
    border: 1px solid rgba(125, 168, 210, 0.28);
    border-radius: 30px;
    background:
        radial-gradient(circle at 90% 5%, rgba(71, 215, 224, 0.22), transparent 18rem),
        linear-gradient(145deg, rgba(255,255,255,0.98), rgba(232,243,253,0.96));
    box-shadow:
        0 30px 65px rgba(15, 48, 88, 0.18),
        0 7px 18px rgba(15, 48, 88, 0.09),
        inset 0 1px 0 rgba(255,255,255,0.95);
}

.mt-login-scene::after {
    position: absolute;
    top: -80px;
    right: -70px;
    width: 220px;
    height: 220px;
    border: 1px solid rgba(67, 155, 215, 0.17);
    border-radius: 50%;
    content: "";
    box-shadow: 0 0 0 28px rgba(67,155,215,0.045), 0 0 0 58px rgba(67,155,215,0.035);
}

.mt-login-brand {
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.42rem 0.75rem;
    border: 1px solid rgba(56, 131, 199, 0.22);
    border-radius: 999px;
    color: var(--mt-blue-700);
    background: rgba(255,255,255,0.76);
    box-shadow: 0 6px 14px rgba(35, 82, 130, 0.08);
    font-size: 0.82rem;
    font-weight: 750;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.mt-login-title {
    position: relative;
    z-index: 1;
    max-width: 620px;
    margin: 1rem 0 0.45rem;
    color: var(--mt-navy-900);
    font-size: clamp(2rem, 5vw, 3.25rem);
    line-height: 1.05;
    font-weight: 800;
    letter-spacing: -0.045em;
}

.mt-login-lead {
    position: relative;
    z-index: 1;
    max-width: 590px;
    margin: 0;
    color: var(--mt-muted);
    font-size: 1rem;
    line-height: 1.65;
}

.mt-login-features {
    position: relative;
    z-index: 1;
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin-top: 1.15rem;
}

.mt-login-feature {
    padding: 0.45rem 0.72rem;
    border: 1px solid rgba(75, 137, 195, 0.18);
    border-radius: 999px;
    color: #3b5879;
    background: rgba(255,255,255,0.72);
    font-size: 0.82rem;
    font-weight: 600;
}

.mt-login-note {
    max-width: 760px;
    margin: 0.75rem auto 0;
    text-align: center;
    color: var(--mt-muted);
    font-size: 0.82rem;
}

[data-testid="stVerticalBlock"]:has(.mt-login-scene)
[data-testid="stForm"] {
    width: min(100%, 760px);
    margin-right: auto;
    margin-left: auto;
    padding: 1.35rem 1.5rem 1.45rem !important;
    border-radius: 24px !important;
    background: rgba(255, 255, 255, 0.94) !important;
}

[data-testid="stVerticalBlock"]:has(.mt-login-scene)
[data-testid="stFormSubmitButton"] > button {
    min-height: 48px;
    font-size: 1rem !important;
}

@media (max-width: 900px) {
    .block-container { padding: 1rem 1rem 2rem; }
    .mt-login-scene { margin-top: 1rem; padding: 1.5rem; border-radius: 22px; }
}

@media (max-width: 640px) {
    .block-container { padding-right: 0.72rem; padding-left: 0.72rem; }
    .mt-login-title { font-size: 2rem; }
    .mt-login-features { display: grid; grid-template-columns: 1fr; }
    .stButton > button, .stDownloadButton > button { width: 100%; }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        scroll-behavior: auto !important;
        transition-duration: 0.01ms !important;
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
    }
}
</style>
"""


def apply_modern_3d_design_system(st: Any) -> None:
    """Install the shared visual layer without changing widget identity."""

    st.markdown(
        MODERN_3D_DESIGN_SYSTEM_CSS,
        unsafe_allow_html=True,
    )
