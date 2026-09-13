from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import inspect

import pytest

from assessment_generation_v2.services.assessment_foundation import (
    ValidationEvidenceIdentity,
    ValidationResult,
    ValidationStatus,
)
from assessment_generation_v2.services.exam_generation_service import (
    AssessmentBlueprintSelection,
    AssessmentBlueprintUnavailableError,
    AssessmentDraftIdentity,
    AssessmentExamGenerationRequest,
    AssessmentExamGenerationService,
    AssessmentGenerationValidationError,
    AssessmentValidationReport,
    ExamGenerationState,
    TeacherValidationConfirmation,
)


OWNER_ID = "11111111-1111-4111-8111-111111111111"
BLUEPRINT_VERSION_ID = (
    "22222222-2222-4222-8222-222222222222"
)
EXAM_ID = "33333333-3333-4333-8333-333333333333"
EXAM_VERSION_ID = (
    "44444444-4444-4444-8444-444444444444"
)
EVIDENCE_DIGEST = "b" * 64


class FakeAssessmentGenerationGateway:
    def __init__(
        self,
        *,
        report: AssessmentValidationReport | ValidationResult | None = None,
        blueprint: AssessmentBlueprintSelection | None = None,
    ) -> None:
        self.report = report or AssessmentValidationReport(
            is_valid=True,
            metrics={"total_score": 10},
        )
        self.blueprint = (
            blueprint
            if blueprint is not None
            else AssessmentBlueprintSelection(
                blueprint_version_id=BLUEPRINT_VERSION_ID,
                blueprint_code="TOAN6_GIUA_HK1",
                lifecycle_status="ACTIVE",
                review_status="APPROVED",
            )
        )
        self.calls: list[str] = []
        self.confirmation_calls: list[
            tuple[str, str, tuple[str, ...]]
        ] = []

    def find_active_approved_blueprint(
        self,
        *,
        blueprint_code: str,
    ) -> AssessmentBlueprintSelection | None:
        self.calls.append("find_blueprint")
        return self.blueprint

    def create_exam_draft(
        self,
        *,
        request: AssessmentExamGenerationRequest,
        blueprint_version_id: str,
    ) -> AssessmentDraftIdentity:
        self.calls.append("create_draft")
        return AssessmentDraftIdentity(
            exam_id=EXAM_ID,
            exam_version_id=EXAM_VERSION_ID,
        )

    def assemble_exam_version(
        self,
        *,
        exam_version_id: str,
        blueprint_version_id: str,
    ) -> None:
        self.calls.append("assemble")

    def validate_exam_version(
        self,
        *,
        exam_version_id: str,
    ) -> AssessmentValidationReport | ValidationResult:
        self.calls.append("validate")
        return self.report

    def confirm_validation_warnings(
        self,
        *,
        exam_version_id: str,
        validation_evidence_digest: str,
        confirmed_warnings: tuple[str, ...],
    ) -> None:
        self.calls.append("confirm_warnings")
        self.confirmation_calls.append(
            (
                exam_version_id,
                validation_evidence_digest,
                confirmed_warnings,
            )
        )

    def submit_exam_for_review(
        self,
        *,
        exam_version_id: str,
    ) -> None:
        self.calls.append("submit_review")


def _request(
    *,
    submit_for_review: bool = True,
    teacher_confirmation: TeacherValidationConfirmation | None = None,
) -> AssessmentExamGenerationRequest:
    return AssessmentExamGenerationRequest(
        blueprint_code="TOAN6_GIUA_HK1",
        owner_user_id=OWNER_ID,
        exam_code="KT_GHK1_TOAN6_001",
        title="Kiá»ƒm tra giá»¯a há»c ká»³ I mÃ´n ToÃ¡n 6",
        submit_for_review=submit_for_review,
        idempotency_key="teacher-1-toan6-ghk1-001",
        teacher_confirmation=teacher_confirmation,
    )


def _warning_result(
    *,
    with_evidence: bool = False,
) -> ValidationResult:
    evidence_identity = None
    if with_evidence:
        evidence_identity = ValidationEvidenceIdentity(
            validation_evidence_id=(
                "55555555-5555-4555-8555-555555555555"
            ),
            validation_input_digest="a" * 64,
            evidence_digest=EVIDENCE_DIGEST,
            validation_schema_version=1,
            validated_at=datetime(
                2026,
                9,
                13,
                3,
                0,
                tzinfo=timezone.utc,
            ),
        )
    return ValidationResult(
        status=ValidationStatus.WARNING,
        warnings=("Review the score distribution.",),
        metrics={"total_score": 10, "warning_count": 1},
        evidence_identity=evidence_identity,
    )


def test_generation_runs_in_governed_order() -> None:
    gateway = FakeAssessmentGenerationGateway()
    service = AssessmentExamGenerationService(
        gateway=gateway
    )

    result = service.generate(request=_request())

    assert gateway.calls == [
        "find_blueprint",
        "create_draft",
        "assemble",
        "validate",
        "submit_review",
    ]
    assert result.state is ExamGenerationState.PENDING_REVIEW
    assert result.validation_report.is_valid


def test_valid_exam_can_stop_ready_for_teacher_review() -> None:
    gateway = FakeAssessmentGenerationGateway()
    service = AssessmentExamGenerationService(
        gateway=gateway
    )

    result = service.generate(
        request=_request(submit_for_review=False)
    )

    assert result.state is ExamGenerationState.READY_FOR_REVIEW
    assert "submit_review" not in gateway.calls


def test_invalid_exam_stops_before_variant_generation() -> None:
    gateway = FakeAssessmentGenerationGateway(
        report=AssessmentValidationReport(
            is_valid=False,
            violations=(
                "Blueprint cell ALGEBRA-UNDERSTAND is short.",
            ),
        )
    )
    service = AssessmentExamGenerationService(
        gateway=gateway
    )

    result = service.generate(request=_request())

    assert (
        result.state
        is ExamGenerationState.REVISION_REQUIRED
    )
    assert "submit_review" not in gateway.calls


def test_legacy_validation_evidence_remains_backward_compatible() -> None:
    valid_report = AssessmentValidationReport(is_valid=True)
    valid_result = AssessmentExamGenerationService(
        gateway=FakeAssessmentGenerationGateway(report=valid_report)
    ).generate(request=_request())

    invalid_report = AssessmentValidationReport(
        is_valid=False,
        violations=("Invalid blueprint coverage.",),
    )
    invalid_gateway = FakeAssessmentGenerationGateway(
        report=invalid_report
    )
    invalid_result = AssessmentExamGenerationService(
        gateway=invalid_gateway
    ).generate(request=_request())

    assert valid_result.validation_report is valid_report
    assert valid_result.validation_report.is_valid
    assert valid_result.state is ExamGenerationState.PENDING_REVIEW
    assert invalid_result.validation_report is invalid_report
    assert not invalid_result.validation_report.is_valid
    assert invalid_result.state is ExamGenerationState.REVISION_REQUIRED
    assert "submit_review" not in invalid_gateway.calls


def test_canonical_pass_continues_without_accepting_stale_confirmation() -> None:
    report = ValidationResult(
        status=ValidationStatus.PASS,
        metrics={"total_score": 10},
    )
    confirmation = TeacherValidationConfirmation(
        teacher_user_id=OWNER_ID,
        confirmed_warnings=("Stale warning.",),
    )
    gateway = FakeAssessmentGenerationGateway(report=report)

    result = AssessmentExamGenerationService(
        gateway=gateway
    ).generate(
        request=_request(teacher_confirmation=confirmation)
    )

    assert result.state is ExamGenerationState.PENDING_REVIEW
    assert result.validation_report is report
    assert result.teacher_confirmation is None
    assert "submit_review" in gateway.calls


def test_canonical_warning_without_confirmation_stays_draft() -> None:
    report = _warning_result()
    gateway = FakeAssessmentGenerationGateway(report=report)

    result = AssessmentExamGenerationService(
        gateway=gateway
    ).generate(request=_request())

    assert result.state is ExamGenerationState.DRAFT
    assert result.validation_report is report
    assert result.validation_report.status is ValidationStatus.WARNING
    assert result.teacher_confirmation is None
    assert "submit_review" not in gateway.calls


@pytest.mark.parametrize("submit_for_review", (False, True))
def test_matching_warning_confirmation_continues_and_preserves_evidence(
    submit_for_review: bool,
) -> None:
    report = _warning_result()
    confirmation = TeacherValidationConfirmation(
        teacher_user_id=OWNER_ID,
        confirmed_warnings=("  Review the score distribution.  ",),
    )
    gateway = FakeAssessmentGenerationGateway(report=report)

    result = AssessmentExamGenerationService(
        gateway=gateway
    ).generate(
        request=_request(
            submit_for_review=submit_for_review,
            teacher_confirmation=confirmation,
        )
    )

    expected_state = (
        ExamGenerationState.PENDING_REVIEW
        if submit_for_review
        else ExamGenerationState.READY_FOR_REVIEW
    )
    assert result.state is expected_state
    assert result.validation_report is report
    assert result.validation_report.status is ValidationStatus.WARNING
    assert result.validation_report.warnings == report.warnings
    assert result.validation_report.metrics is report.metrics
    assert result.teacher_confirmation is confirmation
    assert ("submit_review" in gateway.calls) is submit_for_review


@pytest.mark.parametrize(
    "confirmation",
    (
        TeacherValidationConfirmation(
            teacher_user_id="55555555-5555-4555-8555-555555555555",
            confirmed_warnings=("Review the score distribution.",),
        ),
        TeacherValidationConfirmation(
            teacher_user_id=OWNER_ID,
            confirmed_warnings=("Different warning.",),
        ),
    ),
)
def test_mismatched_warning_confirmation_cannot_authorize(
    confirmation: TeacherValidationConfirmation,
) -> None:
    gateway = FakeAssessmentGenerationGateway(report=_warning_result())

    result = AssessmentExamGenerationService(
        gateway=gateway
    ).generate(
        request=_request(teacher_confirmation=confirmation)
    )

    assert result.state is ExamGenerationState.DRAFT
    assert result.teacher_confirmation is None
    assert "submit_review" not in gateway.calls


def test_canonical_fail_cannot_be_overridden_by_confirmation() -> None:
    report = ValidationResult(
        status=ValidationStatus.FAIL,
        errors=("Blueprint coverage failed.",),
        metrics={"total_score": 9},
    )
    confirmation = TeacherValidationConfirmation(
        teacher_user_id=OWNER_ID,
        confirmed_warnings=("Blueprint coverage failed.",),
    )
    gateway = FakeAssessmentGenerationGateway(report=report)

    result = AssessmentExamGenerationService(
        gateway=gateway
    ).generate(
        request=_request(teacher_confirmation=confirmation)
    )

    assert result.state is ExamGenerationState.REVISION_REQUIRED
    assert result.validation_report is report
    assert result.teacher_confirmation is None
    assert "submit_review" not in gateway.calls


def test_old_request_constructor_still_defaults_confirmation_to_none() -> None:
    request = AssessmentExamGenerationRequest(
        blueprint_code="TOAN6_GIUA_HK1",
        owner_user_id=OWNER_ID,
        exam_code="KT01",
        title="Legacy request",
        submit_for_review=False,
        idempotency_key="legacy-request-1",
    )

    assert request.teacher_confirmation is None


def test_canonical_validation_result_normalizes_legacy_and_preserves_canonical() -> None:
    legacy_pass = AssessmentValidationReport(is_valid=True)
    legacy_fail = AssessmentValidationReport(
        is_valid=False,
        violations=("Invalid coverage.",),
    )
    warning = _warning_result()

    pass_result = AssessmentExamGenerationService(
        gateway=FakeAssessmentGenerationGateway(report=legacy_pass)
    ).generate(request=_request(submit_for_review=False))
    fail_result = AssessmentExamGenerationService(
        gateway=FakeAssessmentGenerationGateway(report=legacy_fail)
    ).generate(request=_request())
    warning_result = AssessmentExamGenerationService(
        gateway=FakeAssessmentGenerationGateway(report=warning)
    ).generate(request=_request())

    assert (
        pass_result.canonical_validation_result.status
        is ValidationStatus.PASS
    )
    assert (
        fail_result.canonical_validation_result.status
        is ValidationStatus.FAIL
    )
    assert warning_result.canonical_validation_result is warning


def test_missing_blueprint_is_rejected() -> None:
    gateway = FakeAssessmentGenerationGateway()
    gateway.blueprint = None
    service = AssessmentExamGenerationService(
        gateway=gateway
    )

    with pytest.raises(
        AssessmentBlueprintUnavailableError
    ):
        service.generate(request=_request())

    assert gateway.calls == ["find_blueprint"]


@pytest.mark.parametrize(
    ("lifecycle_status", "review_status"),
    (
        ("DRAFT", "APPROVED"),
        ("ACTIVE", "PENDING_REVIEW"),
    ),
)
def test_blueprint_must_be_active_and_approved(
    lifecycle_status: str,
    review_status: str,
) -> None:
    gateway = FakeAssessmentGenerationGateway(
        blueprint=AssessmentBlueprintSelection(
            blueprint_version_id=BLUEPRINT_VERSION_ID,
            blueprint_code="TOAN6_GIUA_HK1",
            lifecycle_status=lifecycle_status,
            review_status=review_status,
        )
    )
    service = AssessmentExamGenerationService(
        gateway=gateway
    )

    with pytest.raises(
        AssessmentBlueprintUnavailableError
    ):
        service.generate(request=_request())


def test_request_requires_valid_owner_uuid() -> None:
    with pytest.raises(
        AssessmentGenerationValidationError
    ):
        AssessmentExamGenerationRequest(
            blueprint_code="TOAN6_GIUA_HK1",
            owner_user_id="not-a-uuid",
            exam_code="KT01",
            title="Äá» kiá»ƒm tra",
            idempotency_key="request-1",
        )


def test_draft_generation_has_no_post_publication_artifacts() -> None:
    gateway = FakeAssessmentGenerationGateway()
    service = AssessmentExamGenerationService(
        gateway=gateway
    )

    result = service.generate(request=_request())

    assert not hasattr(result, "variant_ids")
    assert gateway.calls == [
        "find_blueprint",
        "create_draft",
        "assemble",
        "validate",
        "submit_review",
    ]

def test_contracts_are_immutable() -> None:
    request = _request()

    with pytest.raises(FrozenInstanceError):
        request.exam_code = "CHANGED"


def test_validation_metrics_are_read_only() -> None:
    report = AssessmentValidationReport(
        is_valid=True,
        metrics={"total_score": 10},
    )

    with pytest.raises(TypeError):
        report.metrics["total_score"] = 9


def test_service_does_not_approve_publish_or_export() -> None:
    gateway = FakeAssessmentGenerationGateway()
    service = AssessmentExamGenerationService(
        gateway=gateway
    )

    service.generate(request=_request())

    assert "approve" not in gateway.calls
    assert "publish" not in gateway.calls
    assert "export" not in gateway.calls
