from pathlib import Path


def _weekly_text():
    root = Path(__file__).resolve().parents[2]
    return (
        root / "src" / "portal_v2" / "ui" / "weekly_schedule_streamlit.py"
    ).read_text(encoding="utf-8")


def test_r3r1_is_between_output_validation_and_approval():
    text = _weekly_text()
    adapter = text.index("# G1B_13H1_V2_STANDARDIZE_ADAPTER")
    output = text.index("output_name, output_bytes = result[0], result[1]", adapter)
    guard = text.index('raise RuntimeError("Pipeline chuan hoa tra ve DOCX rong.")', output)
    marker = text.index("G1B_P6B_R3R1_V2_ALL_SELECTED_CLASS_DATES", guard)
    approval = text.index("if bool(st.session_state.get(_MT_APPROVAL_ENABLED, True)):", marker)
    assert output < guard < marker < approval


def test_r3r1_reuses_existing_selected_pairs_and_class_overlay():
    text = _weekly_text()
    marker = text.index("G1B_P6B_R3R1_V2_ALL_SELECTED_CLASS_DATES")
    block = text[marker:marker + 2400]
    assert '"_standardization_selected_teaching_date_pairs"' in block
    assert "_mt_overlay_multiclass_teaching_date(" in block
    assert "class_id=class_name" in block
    assert "teaching_date=class_teaching_date" in block


def test_r3r1_preserves_r2r2_and_canonical_context():
    root = Path(__file__).resolve().parents[2]
    weekly = _weekly_text()
    context = (
        root / "src" / "lesson_planning_v2" / "contexts" / "scheduled_lesson_context.py"
    ).read_text(encoding="utf-8")
    assert "G1B_P6B_R2R2_DOCUMENT_DISPLAY_CLASS_BOUNDARY" in weekly
    assert "class_id: str" in context
    assert "class_name:" not in context
