from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DESIGN_PATH = ROOT / "src/portal_v2/ui/modern_3d_design_system.py"
APP_PATH = ROOT / "scripts/teacher_portal/app.py"


def _design_source() -> str:
    return DESIGN_PATH.read_text(encoding="utf-8-sig")


def test_unified_foundation_is_part_of_active_shared_design_system():
    design = _design_source()
    app = APP_PATH.read_text(encoding="utf-8-sig")

    assert "MT-UNIFIED-DESIGN-SYSTEM-V59" in design
    assert "apply_modern_3d_design_system(st)" in app
    assert app.index("apply_teacher_workspace_styles(st)") < app.index(
        "apply_modern_3d_design_system(st)"
    )


def test_unified_foundation_covers_core_streamlit_components():
    design = _design_source()
    required = (
        "--mt-primary:",
        '[data-testid="stMainBlockContainer"]',
        '[data-testid="stForm"]',
        '[data-testid="stMetric"]',
        '[data-testid="stFileUploaderDropzone"]',
        '[data-testid="stDataFrame"]',
        '[data-baseweb="tab-list"]',
        ":focus-visible",
        "prefers-reduced-motion",
    )
    for token in required:
        assert token in design


def test_unified_foundation_is_presentation_only():
    design = _design_source()
    section = design.split("MT-UNIFIED-DESIGN-SYSTEM-V59", 1)[1]
    section = section.split("</style>", 1)[0]

    assert "session_state" not in section
    assert "st.button(" not in section
    assert "st.form(" not in section
    assert "key=" not in section
