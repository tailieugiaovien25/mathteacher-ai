from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "src/portal_v2/ui/modern_3d_design_system.py"
APP = ROOT / "scripts/teacher_portal/app.py"


def test_shared_navy_3d_foundation_is_single_and_presentation_only():
    design = DESIGN.read_text(encoding="utf-8-sig")
    app = APP.read_text(encoding="utf-8-sig")

    marker = "G1B_UI_P1B_SHARED_NAVY_3D_FOUNDATION"
    assert design.count(marker) == 1
    assert app.count(marker) == 1
    assert "def apply_g1b_shared_navy_3d_foundation(st) -> None:" in design
    assert "--g1b-navy: #0b1f3a;" in design
    assert "--g1b-page-bg: #f4f7fb;" in design
    assert ".stDownloadButton > button" in design
    assert "translateY(-1px)" in design
    assert "prefers-reduced-motion" in design
    assert "apply_modern_3d_design_system(st)" in app
    assert "apply_g1b_shared_navy_3d_foundation(st)" in app
    assert app.index("apply_modern_3d_design_system(st)") < app.index(
        "apply_g1b_shared_navy_3d_foundation(st)"
    )


def test_foundation_does_not_embed_business_logic():
    design = DESIGN.read_text(encoding="utf-8-sig")
    forbidden = (
        "LessonPlanMergeService",
        "ScheduledLessonContext",
        "_remove_record(",
        "save_handler(",
        "standardize_handler(",
        "session_state[",
    )
    for token in forbidden:
        assert token not in design
