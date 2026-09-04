from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "src/portal_v2/ui/standardized_lesson_plan_management_streamlit.py"
def test_delete_current_record_is_not_immediately_readded():
    text = TARGET.read_text(encoding="utf-8-sig")
    assert '_DELETED_CURRENT_RECORD_KEY = "standardized_lesson_plan_deleted_current_record_v1"' in text
    assert "G1B_13H1R4B5P_DELETE_CURRENT_READD_GUARD" in text
    assert "st.session_state[_DELETED_CURRENT_RECORD_KEY] = record_id" in text
    assert "G1B_13H1R4B5P_CURRENT_ARTIFACT_TOMBSTONE" in text
    assert "if deleted_current_record_id != current_record_id:" in text
def test_delete_still_cleans_related_state():
    text = TARGET.read_text(encoding="utf-8-sig")
    block = text[text.index("def _remove_record"):text.index("def selected_standardized_lesson_plan_records")]
    assert "st.session_state.pop(_selection_key(record_id), None)" in block
    assert "st.session_state.pop(_PREVIEW_KEY, None)" in block
    assert "_MERGE_ORDER_KEY" in block
    assert "_clear_merge_result()" in block
