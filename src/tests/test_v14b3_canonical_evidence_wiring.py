from __future__ import annotations

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from docx import Document

from document_intelligence.validation import ValidationStatus
from document_standardization.lesson_plan_standardization_audit_evidence_adapter import (
    build_full_audit_evidence,
)
from document_standardization.lesson_plan_standardization_audit_gate import (
    AuditStatus,
    LessonPlanStandardizationAuditGate,
)


UI = Path("src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py")


def _docx(text: str) -> bytes:
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    stream = BytesIO()
    doc.save(stream)
    return stream.getvalue()


def _context() -> dict:
    return {
        "class_name": "6A1",
        "curriculum_period": 10,
        "lesson_title": "Unit 2",
        "drafting_date": "2026-09-01",
        "teaching_date": "2026-09-04",
    }


def _pipeline_evidence():
    return {
        "context_result": SimpleNamespace(unresolved_fields=()),
        "standardization_report": {},
    }


def _full_docx() -> bytes:
    return _docx(
        "Class 6A1\n"
        "Period 10\n"
        "Lesson: Unit 2\n"
        "Date of planning: 01/09/2026\n"
        "Date of teaching: 04/09/2026"
    )


def test_v14b3_retains_expected_found_and_accepted_status():
    bundle = build_full_audit_evidence(
        group_context=_context(),
        standardized_content=_full_docx(),
        pipeline_evidence=_pipeline_evidence(),
    )
    rows = tuple(bundle.validated_analysis.proposals)
    assert len(rows) == 5
    assert all(item.status is ValidationStatus.ACCEPTED for item in rows)
    assert all(item.canonical_value not in (None, "") for item in rows)
    assert all(item.found_value not in (None, "") for item in rows)


def test_v14b3_five_of_five_matches_can_reach_pass():
    bundle = build_full_audit_evidence(
        group_context=_context(),
        standardized_content=_full_docx(),
        pipeline_evidence=_pipeline_evidence(),
    )
    result = LessonPlanStandardizationAuditGate().evaluate(
        original_content=_docx("original"),
        standardized_content=_full_docx(),
        canonical_context=bundle.canonical_context,
        validated_analysis=bundle.validated_analysis,
        context_result=bundle.context_result,
        standardization_report=bundle.standardization_report,
    )
    assert result.status is AuditStatus.PASS


def test_v14b3_missing_field_is_unverified_and_never_fake_pass():
    content = _docx(
        "Class 6A1\n"
        "Period 10\n"
        "Lesson: Unit 2\n"
        "Date of planning: 01/09/2026"
    )
    bundle = build_full_audit_evidence(
        group_context=_context(),
        standardized_content=content,
        pipeline_evidence=_pipeline_evidence(),
    )
    assert any(
        item.status is ValidationStatus.UNVERIFIED
        for item in bundle.validated_analysis.proposals
    )
    result = LessonPlanStandardizationAuditGate().evaluate(
        original_content=_docx("original"),
        standardized_content=content,
        canonical_context=bundle.canonical_context,
        validated_analysis=bundle.validated_analysis,
        context_result=bundle.context_result,
        standardization_report=bundle.standardization_report,
    )
    assert result.status is AuditStatus.WARNING


def test_v14b3_explicit_period_mismatch_is_conflict_and_fail():
    content = _docx(
        "Class 6A1\n"
        "Period 11\n"
        "Lesson: Unit 2\n"
        "Date of planning: 01/09/2026\n"
        "Date of teaching: 04/09/2026"
    )
    bundle = build_full_audit_evidence(
        group_context=_context(),
        standardized_content=content,
        pipeline_evidence=_pipeline_evidence(),
    )
    period_row = next(
        item
        for item in bundle.validated_analysis.proposals
        if getattr(item.proposal.field, "value", "") == "curriculum_period"
    )
    assert period_row.found_value == "11"
    assert period_row.status is ValidationStatus.CONFLICT
    result = LessonPlanStandardizationAuditGate().evaluate(
        original_content=_docx("original"),
        standardized_content=content,
        canonical_context=bundle.canonical_context,
        validated_analysis=bundle.validated_analysis,
        context_result=bundle.context_result,
        standardization_report=bundle.standardization_report,
    )
    assert result.status is AuditStatus.FAIL


def test_v14b3_ui_clears_stale_evidence_before_handler_call():
    text = UI.read_text(encoding="utf-8-sig")
    clear_at = text.index('st.session_state.pop("_g1b_v2_pipeline_evidence", None)')
    call_at = text.index("name, content = standardize_handler(**handler_arguments)")
    assert clear_at < call_at
    assert "V14B3_CLEAR_STALE_CANONICAL_EVIDENCE" in text


def test_v14b3_ui_stores_field_level_evidence_and_vietnamese_report():
    text = UI.read_text(encoding="utf-8-sig")
    assert "V14B3_STORE_FIELD_LEVEL_CANONICAL_EVIDENCE" in text
    assert "V14B3_CANONICAL_FIELD_REPORT" in text
    assert "AUDIT_FIELD_EVIDENCE_KEY" in text
    assert r"\u0110\u1ed1i chi\u1ebfu 5 tr\u01b0\u1eddng d\u1eef li\u1ec7u canonical" in text
    assert r"CH\u01afA X\u00c1C MINH" in text
    assert r"Chu\u1ea9n h\u00f3a \u0111\u1ecbnh d\u1ea1ng theo c\u1ea5u h\u00ecnh ADMIN" in text


def test_v14b3_does_not_weaken_fail_save_block():
    text = UI.read_text(encoding="utf-8-sig")
    assert "release_allowed = canonical_pass_100" in text
    assert "audit_blocks_save = not release_allowed" in text
    assert (
        "save_handler=(None if audit_blocks_save else save_handler)" in text
        or "disabled=(save_handler is None or not standardized_content or audit_blocks_save)" in text
        or "disabled=(not standardized_content or audit_blocks_save)" in text
        or "if audit_blocks_save:" in text
    )
