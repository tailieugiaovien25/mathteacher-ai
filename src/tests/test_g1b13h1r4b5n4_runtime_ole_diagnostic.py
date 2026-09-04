from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "src/portal_v2/ui/standardized_lesson_plan_management_streamlit.py"
def test_retired_runtime_ole_diagnostic_stays_removed():
    text = TARGET.read_text(encoding="utf-8-sig")
    assert "G1B_13H1R4B5N4_RUNTIME_OLE_INSPECTOR" not in text
    assert "G1B_13H1R4B5N4_OLE_ERROR_DETAILS" not in text
    assert "except LessonPlanMergeError as error:" in text
