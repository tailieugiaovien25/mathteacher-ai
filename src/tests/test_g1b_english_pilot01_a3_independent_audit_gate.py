from __future__ import annotations

from io import BytesIO

from docx import Document

from document_intelligence.contracts import DocumentField
from document_standardization.lesson_plan_standardization_audit_gate import (
    AuditStatus,
    LessonPlanStandardizationAuditGate,
)


def _docx_bytes(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


class _ContextResult:
    def __init__(self, unresolved_fields=()):
        self.unresolved_fields = tuple(unresolved_fields)


class _Canonical:
    class_name = "8A1"
    curriculum_period = "10"
    lesson_title = "Unit 2"
    drafting_date = "11/09/2026"
    teaching_date = "14/09/2026"


class _QualityGateStub:
    def __init__(self, status="pass"):
        self._status = status

    def evaluate(self, **kwargs):
        from document_standardization.lesson_plan_standardization_quality_gate import (
            LessonPlanQualityGateResult,
            QualityGateCriterion,
            QualityGateStatus,
        )

        mapped = {
            "pass": QualityGateStatus.PASS,
            "review": QualityGateStatus.REVIEW,
            "fail": QualityGateStatus.FAIL,
        }[self._status]

        return LessonPlanQualityGateResult(
            status=mapped,
            criteria=(
                QualityGateCriterion(
                    field=DocumentField.TEACHING_DATE,
                    code="TEST_CRITERION",
                    status=mapped,
                    message="test",
                    evidence=("evidence",),
                ),
            ),
            conflict_count=1 if self._status == "fail" else 0,
            review_count=1 if self._status == "review" else 0,
            fail_count=1 if self._status == "fail" else 0,
        )


def _evaluate(gate):
    return gate.evaluate(
        original_content=_docx_bytes("original"),
        standardized_content=_docx_bytes("standardized"),
        canonical_context=_Canonical(),
        validated_analysis=None,
        context_result=_ContextResult(),
        standardization_report={},
    )


def test_audit_gate_is_read_only_for_input_bytes():
    original = _docx_bytes("original")
    standardized = _docx_bytes("standardized")
    before_original = bytes(original)
    before_standardized = bytes(standardized)

    gate = LessonPlanStandardizationAuditGate(
        quality_gate=_QualityGateStub("pass")
    )
    gate.evaluate(
        original_content=original,
        standardized_content=standardized,
        canonical_context=_Canonical(),
        validated_analysis=None,
        context_result=_ContextResult(),
        standardization_report={},
    )

    assert original == before_original
    assert standardized == before_standardized


def test_pass_quality_gate_produces_pass_audit():
    result = _evaluate(
        LessonPlanStandardizationAuditGate(
            quality_gate=_QualityGateStub("pass")
        )
    )
    assert result.status is AuditStatus.PASS
    assert result.trust_score == 100
    assert result.source_sha256
    assert result.output_sha256
    assert result.source_sha256 != result.output_sha256


def test_review_quality_gate_produces_warning_not_pass():
    result = _evaluate(
        LessonPlanStandardizationAuditGate(
            quality_gate=_QualityGateStub("review")
        )
    )
    assert result.status is AuditStatus.WARNING
    assert 0 < result.trust_score < 100


def test_fail_quality_gate_produces_fail_even_when_docx_is_readable():
    result = _evaluate(
        LessonPlanStandardizationAuditGate(
            quality_gate=_QualityGateStub("fail")
        )
    )
    assert result.status is AuditStatus.FAIL
    assert result.trust_score < 100


def test_unreadable_output_is_fail_closed():
    gate = LessonPlanStandardizationAuditGate(
        quality_gate=_QualityGateStub("pass")
    )
    result = gate.evaluate(
        original_content=_docx_bytes("original"),
        standardized_content=b"not-a-docx",
        canonical_context=_Canonical(),
        validated_analysis=None,
        context_result=_ContextResult(),
        standardization_report={},
    )
    assert result.status is AuditStatus.FAIL
    assert result.trust_score == 0
    assert result.evidence[0].code == "OUTPUT_DOCX_UNREADABLE"


def test_unreadable_source_is_unverified_not_fake_pass():
    gate = LessonPlanStandardizationAuditGate(
        quality_gate=_QualityGateStub("pass")
    )
    result = gate.evaluate(
        original_content=b"not-a-docx",
        standardized_content=_docx_bytes("standardized"),
        canonical_context=_Canonical(),
        validated_analysis=None,
        context_result=_ContextResult(),
        standardization_report={},
    )
    assert result.status is AuditStatus.UNVERIFIED
    assert result.trust_score == 0
    assert result.evidence[0].code == "SOURCE_DOCX_UNREADABLE"
