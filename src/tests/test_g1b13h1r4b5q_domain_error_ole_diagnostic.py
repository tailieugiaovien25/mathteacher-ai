from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "src/portal_v2/ui/standardized_lesson_plan_management_streamlit.py"
def test_retired_ole_details_are_not_rendered_for_merge_error():
    text = TARGET.read_text(encoding="utf-8-sig")
    assert "G1B_13H1R4B5R2_DOMAIN_OLE_TRIGGER_TRACE" not in text
    assert "except LessonPlanMergeError as error:" in text
    assert "_g1b_runtime_ole_manifest(" not in text
