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


/* ==========================================================
   MT-UNIFIED-DESIGN-SYSTEM-V59
   Shared visual foundation for ADMIN and TEACHER workspaces.
   Presentation only: no widget keys, state, data, or behavior.
   ========================================================== */

:root {
    --mt-font-sans: Inter, "Segoe UI", Roboto, Arial, sans-serif;
    --mt-bg-app: #f4f7fb;
    --mt-bg-surface: #ffffff;
    --mt-bg-subtle: #f8fafc;
    --mt-text-strong: #172033;
    --mt-text: #344054;
    --mt-text-muted: #667085;
    --mt-border: #e3e8f0;
    --mt-border-strong: #cfd7e6;
    --mt-primary: #3157c8;
    --mt-primary-hover: #2647ab;
    --mt-primary-soft: #eef3ff;
    --mt-success: #16845b;
    --mt-warning: #b36908;
    --mt-danger: #c53b45;
    --mt-info: #2563a9;
    --mt-radius-sm: 10px;
    --mt-radius-md: 14px;
    --mt-radius-lg: 18px;
    --mt-shadow-sm: 0 2px 8px rgba(20, 35, 70, 0.05);
    --mt-shadow-md: 0 10px 28px rgba(20, 35, 70, 0.08);
    --mt-focus: 0 0 0 3px rgba(49, 87, 200, 0.20);
}

html,
body,
[class*="css"] {
    font-family: var(--mt-font-sans);
}

[data-testid="stAppViewContainer"] {
    color: var(--mt-text);
    background:
        radial-gradient(circle at 100% 0%, rgba(63, 101, 214, 0.07), transparent 28rem),
        var(--mt-bg-app);
}

[data-testid="stMainBlockContainer"] {
    max-width: 1500px;
    padding-top: 1.35rem;
    padding-bottom: 3rem;
}

[data-testid="stMainBlockContainer"] h1 {
    margin-bottom: 0.35rem;
    color: var(--mt-text-strong);
    font-size: clamp(1.65rem, 2vw, 2.15rem);
    line-height: 1.2;
    letter-spacing: -0.025em;
}

[data-testid="stMainBlockContainer"] h2,
[data-testid="stMainBlockContainer"] h3 {
    color: var(--mt-text-strong);
    letter-spacing: -0.015em;
}

[data-testid="stCaptionContainer"],
[data-testid="stMainBlockContainer"] small {
    color: var(--mt-text-muted);
}

[data-testid="stForm"],
[data-testid="stExpander"],
[data-testid="stDataFrame"],
[data-testid="stDataEditor"],
[data-testid="stMetric"] {
    border-color: var(--mt-border);
    border-radius: var(--mt-radius-md);
    background: var(--mt-bg-surface);
    box-shadow: var(--mt-shadow-sm);
}

[data-testid="stForm"] {
    padding: 1.05rem 1.1rem 1.15rem;
}

[data-testid="stMetric"] {
    min-height: 108px;
    padding: 0.95rem 1rem;
}

[data-testid="stMetricLabel"] {
    color: var(--mt-text-muted);
    font-weight: 650;
}

[data-testid="stMetricValue"] {
    color: var(--mt-text-strong);
}

.stButton > button,
.stDownloadButton > button,
[data-testid="stFormSubmitButton"] > button {
    min-height: 2.65rem;
    border-radius: var(--mt-radius-sm);
    border-color: var(--mt-border-strong);
    font-weight: 650;
    transition: border-color 150ms ease, background 150ms ease,
        color 150ms ease, box-shadow 150ms ease, transform 150ms ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    border-color: var(--mt-primary);
    color: var(--mt-primary);
    box-shadow: var(--mt-shadow-sm);
    transform: translateY(-1px);
}

.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button[kind="primary"] {
    border-color: var(--mt-primary);
    background: linear-gradient(135deg, #3b64d8, var(--mt-primary));
    color: #ffffff;
    box-shadow: 0 7px 16px rgba(49, 87, 200, 0.18);
}

.stButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
    border-color: var(--mt-primary-hover);
    background: var(--mt-primary-hover);
    color: #ffffff;
}

div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div,
[data-testid="stDateInput"] > div > div,
[data-testid="stNumberInput"] > div > div {
    border-color: var(--mt-border-strong);
    border-radius: var(--mt-radius-sm);
    background: #ffffff;
}

div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="textarea"] > div:focus-within,
div[data-baseweb="select"] > div:focus-within,
[data-testid="stDateInput"] > div > div:focus-within,
[data-testid="stNumberInput"] > div > div:focus-within {
    border-color: var(--mt-primary);
    box-shadow: var(--mt-focus);
}

[data-testid="stWidgetLabel"] p {
    color: var(--mt-text);
    font-weight: 620;
}

[data-baseweb="tab-list"] {
    gap: 0.35rem;
    padding: 0.3rem;
    border: 1px solid var(--mt-border);
    border-radius: var(--mt-radius-md);
    background: #edf1f7;
}

[data-baseweb="tab"] {
    min-height: 2.45rem;
    padding: 0.4rem 0.9rem;
    border-radius: 9px;
    color: var(--mt-text-muted);
    font-weight: 650;
}

[aria-selected="true"][data-baseweb="tab"] {
    background: #ffffff;
    color: var(--mt-primary);
    box-shadow: var(--mt-shadow-sm);
}

[data-testid="stExpander"] details summary {
    min-height: 3rem;
    padding-left: 0.85rem;
    padding-right: 0.85rem;
    color: var(--mt-text-strong);
    font-weight: 650;
}

[data-testid="stAlert"] {
    border-radius: var(--mt-radius-md);
    border-width: 1px;
    box-shadow: none;
}

[data-testid="stFileUploaderDropzone"] {
    min-height: 126px;
    border: 1.5px dashed #b9c5db;
    border-radius: var(--mt-radius-md);
    background: var(--mt-bg-subtle);
}

[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--mt-primary);
    background: var(--mt-primary-soft);
}

[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
    overflow: hidden;
}

[data-testid="stHorizontalBlock"] {
    row-gap: 0.8rem;
}

:where(button, input, textarea, [role="button"], [tabindex]):focus-visible {
    outline: 2px solid var(--mt-primary);
    outline-offset: 2px;
}

@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"] {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 1rem;
    }

    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap;
    }
}

@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] h1 {
        font-size: 1.55rem;
    }

    [data-baseweb="tab-list"] {
        overflow-x: auto;
        flex-wrap: nowrap;
    }

    .stButton > button,
    .stDownloadButton > button,
    [data-testid="stFormSubmitButton"] > button {
        width: 100%;
    }
}

@media (prefers-reduced-motion: reduce) {
    .stButton > button,
    .stDownloadButton > button,
    [data-testid="stFormSubmitButton"] > button {
        transition: none;
        transform: none !important;
    }
}


/* ==========================================================
   MT-MODERN-STANDARDIZATION-WORKSPACE-V59
   Scoped visual contract for the full lesson-plan workflow.
   ========================================================== */

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-testid="stMainBlockContainer"] {
    max-width: 1480px;
    padding-top: 1.05rem;
}

.mt-standardization-page-v59 {
    display: none;
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59) h1 {
    margin-bottom: 0.25rem;
    font-size: clamp(1.75rem, 2.15vw, 2.25rem);
    color: var(--mt-text-strong);
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-testid="stCaptionContainer"] {
    max-width: 920px;
    margin-bottom: 0.6rem;
    color: var(--mt-text-muted);
    font-size: 0.94rem;
    line-height: 1.55;
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--mt-border);
    border-radius: var(--mt-radius-lg);
    background: rgba(255, 255, 255, 0.92);
    box-shadow: var(--mt-shadow-sm);
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-testid="stExpander"] {
    margin: 0.55rem 0;
    border: 1px solid var(--mt-border);
    border-radius: var(--mt-radius-md);
    background: #ffffff;
    box-shadow: var(--mt-shadow-sm);
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-testid="stExpander"] details[open] {
    border-radius: var(--mt-radius-md);
    box-shadow: var(--mt-shadow-md);
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-testid="stExpander"] summary {
    min-height: 3.15rem;
    color: var(--mt-text-strong);
    font-weight: 680;
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-testid="stFileUploader"] {
    margin: 0.45rem 0 0.8rem;
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-testid="stFileUploaderDropzone"] {
    min-height: 142px;
    border: 1.5px dashed #aebddd;
    border-radius: 16px;
    background:
        linear-gradient(135deg, rgba(238, 243, 255, 0.86), #ffffff);
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--mt-primary);
    background: var(--mt-primary-soft);
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-baseweb="tab-list"] {
    position: sticky;
    top: 0.4rem;
    z-index: 5;
    margin: 0.4rem 0 0.85rem;
    border: 1px solid var(--mt-border);
    border-radius: 13px;
    background: rgba(237, 241, 247, 0.94);
    backdrop-filter: blur(10px);
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-baseweb="tab"] {
    min-height: 2.65rem;
    font-weight: 680;
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
.stButton > button,
section[data-testid="stMain"]:has(.mt-standardization-page-v59)
.stDownloadButton > button,
section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-testid="stFormSubmitButton"] > button {
    min-height: 2.75rem;
    border-radius: 11px;
    font-weight: 680;
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
.stButton > button[kind="primary"],
section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-testid="stFormSubmitButton"] > button[kind="primary"] {
    border: 0;
    background: linear-gradient(135deg, #4169dd, #294fbd);
    color: #ffffff;
    box-shadow: 0 8px 20px rgba(42, 79, 189, 0.22);
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
.stButton > button:disabled,
section[data-testid="stMain"]:has(.mt-standardization-page-v59)
.stDownloadButton > button:disabled {
    border-color: #e4e8ef;
    background: #f4f6f9;
    color: #98a2b3;
    box-shadow: none;
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-testid="stAlert"] {
    margin: 0.45rem 0;
    border-radius: 13px;
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-testid="stDataFrame"],
section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-testid="stDataEditor"] {
    margin: 0.55rem 0 0.85rem;
    border: 1px solid var(--mt-border);
    border-radius: 14px;
    background: #ffffff;
    box-shadow: var(--mt-shadow-sm);
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
iframe {
    border: 1px solid var(--mt-border) !important;
    border-radius: 14px !important;
    background: #ffffff;
    box-shadow: var(--mt-shadow-sm);
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
hr {
    margin: 1.15rem 0;
    border-color: var(--mt-border);
}

section[data-testid="stMain"]:has(.mt-standardization-page-v59)
[data-testid="stHorizontalBlock"] {
    align-items: stretch;
    row-gap: 0.7rem;
}

@media (max-width: 900px) {
    section[data-testid="stMain"]:has(.mt-standardization-page-v59)
    [data-baseweb="tab-list"] {
        position: static;
        overflow-x: auto;
        flex-wrap: nowrap;
    }
}

@media (max-width: 640px) {
    section[data-testid="stMain"]:has(.mt-standardization-page-v59)
    [data-testid="stMainBlockContainer"] {
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }

    section[data-testid="stMain"]:has(.mt-standardization-page-v59)
    .stButton > button,
    section[data-testid="stMain"]:has(.mt-standardization-page-v59)
    .stDownloadButton > button {
        width: 100%;
    }
}

/* V58-C5E5F2B DARK NAVY 3D GLOBAL THEME */
:root {
 --mt-f2b-navy-1000:#020817; --mt-f2b-navy-950:#041225;
 --mt-f2b-blue:#1778e8; --mt-f2b-cyan:#35d8ff;
}
[data-testid="stAppViewContainer"] > header,
header[data-testid="stHeader"], [data-testid="stToolbar"] {
 background:radial-gradient(circle at 76% 0%,rgba(24,111,203,.22),transparent 28rem),
 linear-gradient(180deg,#020817 0%,#06172c 100%) !important;
 border-bottom:1px solid rgba(70,180,255,.22)!important;
 box-shadow:0 8px 26px rgba(1,10,25,.28)!important;
}
[data-testid="stSidebar"] {
 background:radial-gradient(circle at 18% 4%,rgba(31,128,211,.32),transparent 17rem),
 linear-gradient(180deg,#061a33 0%,#031226 55%,#020b18 100%)!important;
 border-right:1px solid rgba(77,189,255,.30)!important;
 box-shadow:18px 0 42px rgba(1,11,28,.30),inset -1px 0 0 rgba(255,255,255,.035)!important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
 transform:translateX(4px) translateY(-1px)!important;
 border-color:rgba(70,211,255,.32)!important;
 background:linear-gradient(90deg,rgba(22,119,216,.28),rgba(18,64,111,.22))!important;
 box-shadow:0 8px 20px rgba(0,19,48,.24)!important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
 border-radius:18px!important; border-color:rgba(111,156,203,.28)!important;
 box-shadow:0 14px 34px rgba(14,44,82,.09),inset 0 1px 0 rgba(255,255,255,.78)!important;
}
[data-testid="stMainBlockContainer"] hr {
 height:2px!important;border:0!important;margin:1.2rem 0 1.35rem!important;
 background:linear-gradient(90deg,transparent,rgba(23,120,232,.42) 10%,rgba(53,216,255,.82) 50%,rgba(23,120,232,.42) 90%,transparent)!important;
 box-shadow:0 0 14px rgba(53,216,255,.24);
}
.stButton > button:hover,.stDownloadButton > button:hover,[data-testid="stFormSubmitButton"] > button:hover {
 transform:translateY(-2px)!important;
 box-shadow:0 14px 28px rgba(7,62,132,.19),0 0 0 1px rgba(53,216,255,.10),inset 0 1px 0 rgba(255,255,255,.82)!important;
}
.mt-weekly-hero {
 position:relative;overflow:hidden;padding:1.35rem 1.5rem!important;
 border:1px solid rgba(64,194,255,.38)!important;border-radius:20px!important;
 background:radial-gradient(circle at 82% 18%,rgba(45,149,244,.30),transparent 19rem),
 linear-gradient(135deg,#061a34 0%,#092b52 54%,#061a35 100%)!important;
 box-shadow:0 20px 46px rgba(2,23,52,.24),inset 0 1px 0 rgba(255,255,255,.10)!important;
}
.mt-weekly-eyebrow{color:#73dcff!important;text-shadow:0 0 18px rgba(53,216,255,.20)}
.mt-weekly-title{color:#fff!important;text-shadow:0 6px 18px rgba(0,0,0,.24)}
.mt-weekly-subtitle{color:#c6def4!important}
.mt-section-title {
 position:relative;padding:.72rem .95rem!important;margin-top:1.35rem!important;border-radius:12px;
 background:linear-gradient(90deg,#071d39 0%,#0a315b 72%,#0b3c70 100%);
 border:1px solid rgba(64,191,255,.28);box-shadow:0 10px 24px rgba(3,28,62,.16);
}
.mt-section-title::after {
 content:"";position:absolute;left:.9rem;right:.9rem;bottom:-.42rem;height:2px;border-radius:999px;
 background:linear-gradient(90deg,#1778e8,#35d8ff,rgba(53,216,255,0));
 box-shadow:0 0 12px rgba(53,216,255,.34);
}
.mt-section-title h3{color:#fff!important}.mt-section-title span{color:#bfe5ff!important}
section[data-testid="stMain"]:has(.mt-weekly-hero) [data-testid="stVerticalBlockBorderWrapper"] {
 border-color:rgba(50,132,211,.28)!important;border-radius:18px!important;
 background:linear-gradient(180deg,rgba(255,255,255,.98),rgba(247,251,255,.98))!important;
 box-shadow:0 15px 34px rgba(9,48,91,.10),inset 0 1px 0 rgba(255,255,255,.95)!important;
}


/* V58-C5E5F2C WEEKLY DARK ACTION BUTTONS */
section[data-testid="stMain"]:has(.mt-weekly-hero)
[data-testid="stVerticalBlockBorderWrapper"]:has(.mt-weekly-actions)
.stButton > button {
    min-height: 2.85rem !important;
    color: #f4fbff !important;
    border: 1px solid rgba(76, 194, 255, 0.46) !important;
    border-radius: 13px !important;
    background: linear-gradient(180deg, #0b2949 0%, #06192f 55%, #030d1d 100%) !important;
    box-shadow: 0 12px 24px rgba(1, 17, 40, 0.28),
                inset 0 1px 0 rgba(255, 255, 255, 0.11),
                inset 0 -1px 0 rgba(31, 125, 210, 0.18) !important;
    text-shadow: 0 1px 1px rgba(0, 0, 0, 0.36);
}
section[data-testid="stMain"]:has(.mt-weekly-hero)
[data-testid="stVerticalBlockBorderWrapper"]:has(.mt-weekly-actions)
.stButton > button:hover {
    color: #ffffff !important;
    border-color: rgba(74, 218, 255, 0.82) !important;
    background: linear-gradient(180deg, #0f3d6d 0%, #09284b 55%, #041426 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 16px 30px rgba(0, 30, 72, 0.34),
                0 0 18px rgba(53, 216, 255, 0.16),
                inset 0 1px 0 rgba(255, 255, 255, 0.14) !important;
}
section[data-testid="stMain"]:has(.mt-weekly-hero)
[data-testid="stVerticalBlockBorderWrapper"]:has(.mt-weekly-actions)
.stButton > button:active {
    transform: translateY(1px) !important;
    background: linear-gradient(180deg, #06192f 0%, #020a16 100%) !important;
}


/* V58-C5E5F2D WEEKLY ACTION KEY TARGETING */
[class*="st-key-weekly_standardize_"] button,
[class*="st-key-weekly_ai_"] button {
    min-height: 2.95rem !important;
    background: linear-gradient(180deg, #0b2a4c 0%, #061a31 54%, #020a16 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(54, 199, 255, 0.72) !important;
    border-radius: 14px !important;
    box-shadow: 0 12px 24px rgba(0, 13, 32, 0.42), 0 0 0 1px rgba(42, 151, 255, 0.10), inset 0 1px 0 rgba(255, 255, 255, 0.12), inset 0 -1px 0 rgba(0, 105, 210, 0.22) !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.48) !important;
}
[class*="st-key-weekly_standardize_"] button *,
[class*="st-key-weekly_ai_"] button * { color: #ffffff !important; }
[class*="st-key-weekly_standardize_"] button:hover,
[class*="st-key-weekly_ai_"] button:hover {
    background: linear-gradient(180deg, #10467d 0%, #0a2c51 52%, #041326 100%) !important;
    color: #ffffff !important;
    border-color: #4fd8ff !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 16px 30px rgba(0, 22, 55, 0.50), 0 0 20px rgba(55, 210, 255, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.16) !important;
}
[class*="st-key-weekly_standardize_"] button:active,
[class*="st-key-weekly_ai_"] button:active {
    transform: translateY(1px) !important;
    background: linear-gradient(180deg, #06182d 0%, #010711 100%) !important;
}

</style>
"""


def apply_modern_3d_design_system(st: Any) -> None:
    """Install the shared visual layer without changing widget identity."""

    st.markdown(
        MODERN_3D_DESIGN_SYSTEM_CSS,
        unsafe_allow_html=True,
    )

# G1B_UI_P1B_SHARED_NAVY_3D_FOUNDATION
def apply_g1b_shared_navy_3d_foundation(st) -> None:
    """Presentation-only UI foundation layered after the existing design system."""
    st.markdown(
        """
        <style>
        :root {
            --g1b-page-bg: #f4f7fb;
            --g1b-surface: #ffffff;
            --g1b-navy: #0b1f3a;
            --g1b-navy-2: #102a43;
            --g1b-navy-hover: #163b65;
            --g1b-accent: #2f6fed;
            --g1b-text: #14213d;
            --g1b-muted: #607087;
            --g1b-border: #d8e1ec;
            --g1b-success: #178a55;
            --g1b-warning: #b7791f;
            --g1b-danger: #b42318;
            --g1b-radius: 14px;
            --g1b-shadow:
                0 1px 2px rgba(15, 31, 58, .10),
                0 8px 20px rgba(15, 31, 58, .10);
            --g1b-shadow-hover:
                0 2px 4px rgba(15, 31, 58, .14),
                0 12px 26px rgba(15, 31, 58, .14);
        }

        html, body, [data-testid="stAppViewContainer"] {
            background: var(--g1b-page-bg);
            color: var(--g1b-text);
        }

        [data-testid="stHeader"] {
            background: rgba(244, 247, 251, .92);
        }

        [data-testid="stMainBlockContainer"] {
            color: var(--g1b-text);
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--g1b-navy);
            letter-spacing: -.012em;
        }

        [data-testid="stCaptionContainer"],
        .stCaption {
            color: var(--g1b-muted);
        }

        div[data-testid="stMetric"],
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--g1b-surface);
            border-color: var(--g1b-border);
            border-radius: var(--g1b-radius);
        }

        div[data-testid="stMetric"] {
            box-shadow: var(--g1b-shadow);
            padding: .8rem 1rem;
        }

        .stButton > button,
        .stDownloadButton > button,
        .stLinkButton > a {
            background: linear-gradient(180deg, #163b65 0%, #0b1f3a 100%);
            color: #ffffff !important;
            border: 1px solid #07182d;
            border-top-color: #315579;
            border-radius: 12px;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.18),
                0 2px 0 #07182d,
                0 7px 16px rgba(11,31,58,.18);
            font-weight: 650;
            min-height: 2.55rem;
            transition:
                transform .12s ease,
                box-shadow .12s ease,
                background .12s ease,
                border-color .12s ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stLinkButton > a:hover {
            background: linear-gradient(180deg, #1d4c7f 0%, #102a43 100%);
            border-color: #0b1f3a;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.22),
                0 3px 0 #07182d,
                var(--g1b-shadow-hover);
            transform: translateY(-1px);
            color: #ffffff !important;
        }

        .stButton > button:active,
        .stDownloadButton > button:active,
        .stLinkButton > a:active {
            transform: translateY(1px);
            box-shadow:
                inset 0 1px 2px rgba(0,0,0,.15),
                0 1px 0 #07182d,
                0 3px 8px rgba(11,31,58,.16);
        }

        .stButton > button:focus-visible,
        .stDownloadButton > button:focus-visible,
        .stLinkButton > a:focus-visible {
            outline: 3px solid rgba(47,111,237,.28);
            outline-offset: 2px;
        }

        .stButton > button:disabled,
        .stDownloadButton > button:disabled {
            background: #d9e1eb !important;
            color: #68778a !important;
            border-color: #c5cfdb !important;
            box-shadow: none !important;
            transform: none !important;
            opacity: 1 !important;
        }

        [data-baseweb="tab-list"] {
            gap: .35rem;
        }

        [data-baseweb="tab"] {
            border-radius: 10px 10px 0 0;
            font-weight: 650;
        }

        [data-baseweb="tab"][aria-selected="true"] {
            color: var(--g1b-navy);
        }

        div[data-baseweb="select"] > div,
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input {
            border-radius: 10px;
        }

        .g1b-hero {
            border-color: var(--g1b-border) !important;
            box-shadow: var(--g1b-shadow) !important;
        }

        .g1b-viewer {
            background: #ffffff !important;
            border-color: var(--g1b-border) !important;
            box-shadow: 0 8px 24px rgba(15,31,58,.07);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #071a33 0%, #0b1f3a 100%) !important;
        }

        [data-testid="stSidebar"] .stButton > button {
            border-color: rgba(255,255,255,.22);
        }

        @media (prefers-reduced-motion: reduce) {
            .stButton > button,
            .stDownloadButton > button,
            .stLinkButton > a {
                transition: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
