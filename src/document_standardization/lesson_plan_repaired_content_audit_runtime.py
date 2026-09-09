from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from document_standardization.lesson_plan_standardization_audit_evidence_adapter import (
    build_full_audit_evidence,
)
from document_standardization.lesson_plan_standardization_audit_gate import (
    LessonPlanStandardizationAuditGate,
)


@dataclass(frozen=True)
class RepairedContentAuditResult:
    audit_result: Any
    canonical_field_rows: dict[str, dict[str, Any]]
    compliance: dict[str, Any]
    evidence_ready: bool
    missing_evidence: tuple[str, ...]


def _canonical_field_rows(evidence_bundle: Any) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    validated_analysis = getattr(evidence_bundle, "validated_analysis", None)
    for validated_item in tuple(
        getattr(validated_analysis, "proposals", ()) or ()
    ):
        proposal = getattr(validated_item, "proposal", None)
        field_value = getattr(proposal, "field", None)
        field_key = getattr(field_value, "value", field_value)
        field_key = str(field_key or "").strip()
        if not field_key:
            continue
        status_raw = getattr(validated_item, "status", None)
        status_text = getattr(status_raw, "value", status_raw)
        rows[field_key] = {
            "expected": getattr(validated_item, "canonical_value", None),
            "found": getattr(
                validated_item,
                "found_value",
                getattr(proposal, "value", None),
            ),
            "status": str(status_text or "unverified").lower(),
        }
    return rows


def audit_repaired_content(
    *,
    original_content: bytes,
    repaired_content: bytes,
    group_context: Mapping[str, Any],
    pipeline_evidence: Mapping[str, Any] | None,
) -> RepairedContentAuditResult:
    original = bytes(original_content or b"")
    repaired = bytes(repaired_content or b"")
    if not original:
        raise ValueError("original content must not be empty")
    if not repaired:
        raise ValueError("repaired content must not be empty")
    if not isinstance(group_context, Mapping):
        raise TypeError("group context must be a mapping")

    evidence_bundle = build_full_audit_evidence(
        group_context=group_context,
        standardized_content=repaired,
        pipeline_evidence=(
            pipeline_evidence
            if isinstance(pipeline_evidence, Mapping)
            else None
        ),
    )
    audit_gate = LessonPlanStandardizationAuditGate()
    if evidence_bundle.ready:
        audit_result = audit_gate.evaluate(
            original_content=original,
            standardized_content=repaired,
            canonical_context=evidence_bundle.canonical_context,
            validated_analysis=evidence_bundle.validated_analysis,
            context_result=evidence_bundle.context_result,
            standardization_report=evidence_bundle.standardization_report,
        )
    else:
        audit_result = audit_gate.evaluate_artifact_only(
            original_content=original,
            standardized_content=repaired,
        )

    standardization_report = evidence_bundle.standardization_report
    compliance_raw = (
        standardization_report.get("compliance", {})
        if isinstance(standardization_report, Mapping)
        else {}
    )
    compliance = (
        dict(compliance_raw)
        if isinstance(compliance_raw, Mapping)
        else {}
    )
    compliance_status = str(
        compliance.get("status") or "UNVERIFIED"
    ).upper()
    if compliance_status != "PASS":
        audit_result = {
            "status": "fail",
            "trust_score": 0,
            "message": (
                "ADMIN Configuration Enforcement Gate: "
                + compliance_status
            ),
            "evidence": tuple(compliance.get("checks") or ()),
        }

    return RepairedContentAuditResult(
        audit_result=audit_result,
        canonical_field_rows=_canonical_field_rows(evidence_bundle),
        compliance=compliance,
        evidence_ready=bool(evidence_bundle.ready),
        missing_evidence=tuple(evidence_bundle.missing_evidence or ()),
    )
