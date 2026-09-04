from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace

from docx import Document

from document_intelligence.validation import ValidationStatus
from document_standardization.lesson_plan_standardization_audit_evidence_adapter import (
    build_full_audit_evidence,
)


def _docx(text: str) -> bytes:
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    stream = BytesIO()
    doc.save(stream)
    return stream.getvalue()


def test_a5h_adapter_accepts_values_proven_in_final_artifact():
    content = _docx(
        "Class 6A1\n"
        "Period 10\n"
        "Lesson: Unit 2\n"
        "Date of planning: 01/09/2026\n"
        "Date of teaching: 04/09/2026"
    )
    bundle = build_full_audit_evidence(
        group_context={
            "class_name": "6A1",
            "curriculum_period": 10,
            "lesson_title": "Unit 2",
            "drafting_date": "2026-09-01",
            "teaching_date": "2026-09-04",
        },
        standardized_content=content,
        pipeline_evidence={
            "context_result": SimpleNamespace(unresolved_fields=()),
            "standardization_report": {},
        },
    )
    assert bundle.ready is True
    assert all(
        item.status is ValidationStatus.ACCEPTED
        for item in bundle.validated_analysis.proposals
    )


def test_a5h_adapter_is_conservative_when_final_artifact_does_not_prove_value():
    content = _docx("Class 6A1\nPeriod 10")
    bundle = build_full_audit_evidence(
        group_context={
            "class_name": "6A1",
            "curriculum_period": 10,
            "lesson_title": "Unit 2",
            "drafting_date": "2026-09-01",
            "teaching_date": "2026-09-04",
        },
        standardized_content=content,
        pipeline_evidence={
            "context_result": SimpleNamespace(unresolved_fields=()),
            "standardization_report": {},
        },
    )
    statuses = [item.status for item in bundle.validated_analysis.proposals]
    assert ValidationStatus.UNVERIFIED in statuses


def test_a5h_adapter_not_ready_without_pipeline_evidence():
    content = _docx("Class 6A1\nPeriod 10\nUnit 2\n01/09/2026\n04/09/2026")
    bundle = build_full_audit_evidence(
        group_context={
            "class_name": "6A1",
            "curriculum_period": 10,
            "lesson_title": "Unit 2",
            "drafting_date": "2026-09-01",
            "teaching_date": "2026-09-04",
        },
        standardized_content=content,
        pipeline_evidence={},
    )
    assert bundle.ready is False
    assert "context_result" in bundle.missing_evidence
    assert "standardization_report" in bundle.missing_evidence
