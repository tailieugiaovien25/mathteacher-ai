from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document

from document_standardization.lesson_plan_standardization_audit_gate import (
    AuditStatus,
    LessonPlanStandardizationAuditGate,
)

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "src" / "portal_v2" / "ui" / "standardized_lesson_plan_authoring_v2_streamlit.py"


def _docx(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_artifact_only_audit_never_claims_pass_without_canonical_evidence():
    result = LessonPlanStandardizationAuditGate().evaluate_artifact_only(
        original_content=_docx("original"),
        standardized_content=_docx("standardized"),
    )
    assert result.status is AuditStatus.WARNING
    assert result.trust_score < 100
    assert any(item.code == "CANONICAL_EVIDENCE_NOT_WIRED" for item in result.evidence)


def test_artifact_only_audit_fails_closed_on_bad_output():
    result = LessonPlanStandardizationAuditGate().evaluate_artifact_only(
        original_content=_docx("original"),
        standardized_content=b"not-a-docx",
    )
    assert result.status is AuditStatus.FAIL
    assert result.trust_score == 0


def test_v2_runtime_wires_audit_and_status_ui():
    text = UI.read_text(encoding="utf-8")
    assert 'AUDIT_RESULT_KEY = "g1b_v2_standardization_audit_result"' in text
    assert "G1B_ENGLISH_PILOT01_A5H_FULL_AUDIT_RUNTIME" in text
    assert "evaluate_artifact_only(" in text
    assert "original_content=original_content" in text
    assert "standardized_content=standardized_bytes" in text
    assert "G1B_ENGLISH_PILOT01_A5H_AUDIT_STATUS_UI" in text
    assert "canonical_pass_100" in text
    assert 'normalized_status == "warning"' in text
    assert 'normalized_status == "fail"' in text
    assert "UNVERIFIED" in text

