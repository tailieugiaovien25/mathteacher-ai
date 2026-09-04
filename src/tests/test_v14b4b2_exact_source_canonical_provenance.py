from pathlib import Path

ADAPTER = Path("src/document_standardization/lesson_plan_standardization_audit_evidence_adapter.py")
WEEKLY = Path("src/portal_v2/ui/weekly_schedule_streamlit.py")

def test_exact_title_branch_now_reads_unit_and_lesson_from_docx():
    text = ADAPTER.read_text(encoding="utf-8-sig")
    marker = text.index("if field is DocumentField.LESSON_TITLE:")
    branch_end = text.index("\n    return None", marker)
    window = text[marker:branch_end]
    assert "unit_match = re.search" in window
    assert "lesson_match = re.search" in window
    assert "canonical_value" not in window

def test_audit_prefers_runtime_resolved_canonical_snapshot():
    text = ADAPTER.read_text(encoding="utf-8-sig")
    assert 'pipeline.get("resolved_canonical_context")' in text
    assert "if isinstance(resolved_canonical_context, Mapping)" in text

def test_runtime_snapshot_has_exact_five_fields():
    text = WEEKLY.read_text(encoding="utf-8-sig")
    marker = text.index("V14B4B2_RESOLVED_CANONICAL_PROVENANCE")
    window = text[marker:marker + 1800]
    for key in ('"class_name"', '"curriculum_period"', '"lesson_title"', '"drafting_date"', '"teaching_date"'):
        assert key in window
    assert 'pipeline_evidence_v14b4b2["resolved_canonical_context"]' in window

def test_drafting_snapshot_uses_proven_admin_runtime_rule():
    text = WEEKLY.read_text(encoding="utf-8-sig")
    marker = text.index("V14B4B2_RESOLVED_CANONICAL_PROVENANCE")
    window = text[marker:marker + 1800]
    assert "_MT_DRAFTING_ENABLED" in window
    assert "_MT_DRAFTING_DAYS" in window
    assert "_mt_date_before_teaching_week(" in window

def test_validation_semantics_remain_conflict_unverified_accepted():
    text = ADAPTER.read_text(encoding="utf-8-sig")
    assert "ValidationStatus.CONFLICT" in text
    assert "ValidationStatus.UNVERIFIED" in text
    assert "ValidationStatus.ACCEPTED" in text
