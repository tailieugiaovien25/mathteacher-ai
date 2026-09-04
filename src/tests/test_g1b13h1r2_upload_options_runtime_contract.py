from pathlib import Path


SOURCE = Path("src/portal_v2/ui/weekly_schedule_streamlit.py")


def test_upload_runtime_filters_v2_kwargs_at_legacy_signature_boundary():
    text = SOURCE.read_text(encoding="utf-8")
    anchor = "signature = inspect.signature(\n        _mt_original_process_lesson_plan_upload_dates\n    )"
    assert text.count(anchor) == 1
    block = text[text.index(anchor):]
    block = block[: block.index("\n\n    row = ")]
    assert "supported_kwargs = {" in block
    assert "if name in signature.parameters" in block
    assert "**supported_kwargs," in block
    assert "**kwargs," not in block


def test_v2_public_processor_keeps_extended_runtime_contract():
    text = SOURCE.read_text(encoding="utf-8")
    public_contract = """    options=None,\n    original_content=None,\n    ai_revised_text=\"\","""
    assert public_contract in text
