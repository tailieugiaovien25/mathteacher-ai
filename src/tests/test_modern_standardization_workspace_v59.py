from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "src/portal_v2/ui/weekly_schedule_streamlit.py"
DESIGN = ROOT / "src/portal_v2/ui/modern_3d_design_system.py"


def test_standardization_page_installs_one_scoped_visual_anchor():
    text = PAGE.read_text(encoding="utf-8-sig")
    assert text.count("MT-STANDARDIZATION-WORKSPACE-V59") == 1
    assert text.count('class="mt-standardization-page-v59"') == 1
    assert "def _render_standardization_modern_3d_header(" in text
    ast.parse(text)


def test_standardization_design_is_scoped_and_responsive():
    design = DESIGN.read_text(encoding="utf-8-sig")
    assert "MT-MODERN-STANDARDIZATION-WORKSPACE-V59" in design
    assert 'section[data-testid="stMain"]:has(.mt-standardization-page-v59)' in design
    assert '[data-testid="stFileUploaderDropzone"]' in design
    assert '[data-baseweb="tab-list"]' in design
    assert '[data-testid="stDataFrame"]' in design
    assert "@media (max-width: 640px)" in design


def test_visual_change_preserves_locked_workflow_controls():
    text = PAGE.read_text(encoding="utf-8-sig")
    required = (
        "standardization_action_upload",
        "standardization_action_create",
        "standardization_action_preview",
        "standardization_action_save",
        "standardization_action_download",
        "_render_standardization_control_panel(",
        "_process_lesson_plan_upload(",
        "render_standardized_lesson_plan_management(",
        "_latest_ai_standardization_transfer()",
        "standardization_image_autofit_enabled",
    )
    for token in required:
        assert token in text


def test_scoped_visual_contract_does_not_change_behavior():
    design = DESIGN.read_text(encoding="utf-8-sig")
    section = design.split("MT-MODERN-STANDARDIZATION-WORKSPACE-V59", 1)[1]
    section = section.split("</style>", 1)[0]
    assert "session_state" not in section
    assert "st.button(" not in section
    assert "key=" not in section
