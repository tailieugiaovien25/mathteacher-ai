from pathlib import Path


def _weekly_text():
    root = Path(__file__).resolve().parents[2]
    return (
        root
        / "src"
        / "portal_v2"
        / "ui"
        / "weekly_schedule_streamlit.py"
    ).read_text(encoding="utf-8")


def test_r2r2_display_class_override_is_inside_v2_adapter_before_process_call():
    text = _weekly_text()
    adapter = text.index("# G1B_13H1_V2_STANDARDIZE_ADAPTER")
    marker = text.index("G1B_P6B_R2R2_DOCUMENT_DISPLAY_CLASS_BOUNDARY", adapter)
    call = text.index("# G1B_13H1R1_SIGNATURE_SAFE_CALL", marker)
    assert adapter < marker < call
    block = text[marker:call]
    assert '"class_name"' in block
    assert '"class_display"' in block
    assert "row.class_id = document_class_display" in block


def test_r2r2_does_not_modify_locator_contract():
    root = Path(__file__).resolve().parents[2]
    text = (
        root
        / "src"
        / "document_standardization"
        / "lesson_plan_metadata_locator.py"
    ).read_text(encoding="utf-8")
    assert "G1B_P6B_R2_KEEP_ENGLISH_DISPLAY_CLASS" not in text
    assert "G1B_P6B_R2_COMPACT_SHARED_FIELDS_ONLY" not in text


def test_canonical_context_schema_remains_internal_class_id_only():
    root = Path(__file__).resolve().parents[2]
    text = (
        root
        / "src"
        / "lesson_planning_v2"
        / "contexts"
        / "scheduled_lesson_context.py"
    ).read_text(encoding="utf-8")
    assert "class_id: str" in text
    assert "class_name:" not in text
