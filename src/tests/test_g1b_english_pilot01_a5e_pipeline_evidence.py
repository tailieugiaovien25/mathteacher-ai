from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=(ROOT/"src/lesson_planning_v2/services/lesson_plan_document_processing_service.py").read_text(encoding="utf-8-sig")
W=(ROOT/"src/portal_v2/ui/weekly_schedule_streamlit.py").read_text(encoding="utf-8-sig")
def test_a5e_processing_result_keeps_pipeline_evidence():
    assert "G1B_A5E_PIPELINE_EVIDENCE_FIELDS" in S
    assert "context_result=result.context_result" in S
    assert 'standardization_report=getattr(result, "standardization_report", None)' in S
def test_a5e_upload_contract_stays_tuple_and_side_channel_exists():
    assert "G1B_A5E_UPLOAD_EVIDENCE_SIDE_CHANNEL" in W
    assert "return (\n        result.output_name,\n        result.output_bytes,\n        result.unresolved_fields,\n    )" in W
def test_a5e_v2_public_contract_stays_name_bytes():
    assert "return str(output_name or file_name), output_bytes" in W
