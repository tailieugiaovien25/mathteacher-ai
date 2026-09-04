from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py"

def test_approved_standardized_workspace_visual_contract():
    text = TARGET.read_text(encoding="utf-8-sig")
    assert "G1B_UI_P2A_APPROVED_STANDARDIZED_WORKSPACE" in text
    assert ".g1b-context-grid" in text
    assert ".g1b-context-card" in text
    assert "#0b1f3a" in text
    assert "#061426" in text
    assert 'button[kind="primary"]' in text
    assert "translateY(-1px)" in text
    assert ".g1b-viewer" in text

def test_stable_standardization_and_management_wiring_remains_present():
    text = TARGET.read_text(encoding="utf-8-sig")
    required = (
        "standardize_handler",
        "save_handler",
        "preview_html_builder",
        "render_standardized_lesson_plan_management",
        "G1B_13H1R4B5J_TOP_SAVE_RUNTIME_WIRING",
        "G1B_13H1R4B_STANDARDIZED_LIST_WIRING",
        "G1B_13H1R4B4J_SAVE_AND_BACK_NAV",
    )
    for token in required:
        assert token in text
