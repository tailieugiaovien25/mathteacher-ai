from types import SimpleNamespace
from unittest.mock import Mock, patch

from document_standardization.lesson_plan_repaired_content_audit_runtime import (
    audit_repaired_content,
)


def _validated_item(field="lesson_title", status="accepted"):
    return SimpleNamespace(
        proposal=SimpleNamespace(
            field=SimpleNamespace(value=field),
            value="Found",
        ),
        status=SimpleNamespace(value=status),
        canonical_value="Expected",
        found_value="Found",
    )


def _bundle(*, ready=True, compliance_status="PASS"):
    return SimpleNamespace(
        ready=ready,
        missing_evidence=() if ready else ("context_result",),
        canonical_context=object(),
        validated_analysis=SimpleNamespace(
            proposals=(_validated_item(),)
        ),
        context_result=object() if ready else None,
        standardization_report={
            "compliance": {
                "status": compliance_status,
                "checks": ({"code": "PAGE_SIZE", "status": compliance_status},),
            }
        },
    )


def test_ready_reaudit_uses_repaired_bytes_and_rebuilds_field_rows():
    gate = Mock()
    gate.evaluate.return_value = {"status": "pass", "trust_score": 100}
    with patch(
        "document_standardization.lesson_plan_repaired_content_audit_runtime."
        "build_full_audit_evidence",
        return_value=_bundle(),
    ) as build, patch(
        "document_standardization.lesson_plan_repaired_content_audit_runtime."
        "LessonPlanStandardizationAuditGate",
        return_value=gate,
    ):
        result = audit_repaired_content(
            original_content=b"original",
            repaired_content=b"repaired",
            group_context={"group_id": "G1"},
            pipeline_evidence={"standardization_report": {}},
        )

    assert build.call_args.kwargs["standardized_content"] == b"repaired"
    assert gate.evaluate.call_args.kwargs["standardized_content"] == b"repaired"
    assert result.audit_result["status"] == "pass"
    assert result.canonical_field_rows["lesson_title"] == {
        "expected": "Expected",
        "found": "Found",
        "status": "accepted",
    }
    assert result.compliance["status"] == "PASS"
    assert result.evidence_ready is True


def test_not_ready_reaudit_uses_artifact_only_and_reports_missing_evidence():
    gate = Mock()
    gate.evaluate_artifact_only.return_value = {
        "status": "warning",
        "trust_score": 50,
    }
    with patch(
        "document_standardization.lesson_plan_repaired_content_audit_runtime."
        "build_full_audit_evidence",
        return_value=_bundle(ready=False),
    ), patch(
        "document_standardization.lesson_plan_repaired_content_audit_runtime."
        "LessonPlanStandardizationAuditGate",
        return_value=gate,
    ):
        result = audit_repaired_content(
            original_content=b"original",
            repaired_content=b"repaired",
            group_context={},
            pipeline_evidence=None,
        )

    gate.evaluate.assert_not_called()
    gate.evaluate_artifact_only.assert_called_once()
    assert result.missing_evidence == ("context_result",)


def test_admin_compliance_failure_overrides_other_audit_result():
    gate = Mock()
    gate.evaluate.return_value = {"status": "pass", "trust_score": 100}
    with patch(
        "document_standardization.lesson_plan_repaired_content_audit_runtime."
        "build_full_audit_evidence",
        return_value=_bundle(compliance_status="FAIL"),
    ), patch(
        "document_standardization.lesson_plan_repaired_content_audit_runtime."
        "LessonPlanStandardizationAuditGate",
        return_value=gate,
    ):
        result = audit_repaired_content(
            original_content=b"original",
            repaired_content=b"repaired",
            group_context={},
            pipeline_evidence={},
        )

    assert result.audit_result["status"] == "fail"
    assert result.audit_result["trust_score"] == 0
    assert "ADMIN Configuration Enforcement Gate" in result.audit_result["message"]


def test_empty_artifacts_fail_closed():
    for original, repaired, message in (
        (b"", b"repaired", "original content"),
        (b"original", b"", "repaired content"),
    ):
        try:
            audit_repaired_content(
                original_content=original,
                repaired_content=repaired,
                group_context={},
                pipeline_evidence=None,
            )
        except ValueError as error:
            assert message in str(error)
        else:
            raise AssertionError("empty artifact must fail closed")
