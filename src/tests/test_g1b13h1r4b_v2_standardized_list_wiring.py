from pathlib import Path

V2 = Path("src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py")
MANAGEMENT = Path("src/portal_v2/ui/standardized_lesson_plan_management_streamlit.py")

def test_v2_renders_existing_standardized_management_module():
    text = V2.read_text(encoding="utf-8")
    assert "G1B_13H1R4B_STANDARDIZED_LIST_WIRING" in text
    assert "render_standardized_lesson_plan_management" in text
    assert "current_content=standardized_content" in text
    assert "preview_html_builder=preview_html_builder" in text

def test_list_is_guarded_by_standardized_content():
    text = V2.read_text(encoding="utf-8")
    block = text[text.index("G1B_13H1R4B_STANDARDIZED_LIST_WIRING"):]
    assert "if standardized_content:" in block
    assert block.index("if standardized_content:") < block.index("render_standardized_lesson_plan_management(")

def test_existing_management_actions_and_merge_remain_available():
    text = MANAGEMENT.read_text(encoding="utf-8")
    for token in ("_remember_current_artifact", "_remove_record", "download_button", "LessonPlanMergeService"):
        assert token in text

def test_unverified_persistent_save_remains_disabled():
    text = V2.read_text(encoding="utf-8")
    block = text[text.index("G1B_13H1R4B_STANDARDIZED_LIST_WIRING"):]
    assert "save_handler=save_handler" in block
    assert "disabled=save_handler is None" in MANAGEMENT.read_text(encoding="utf-8")
