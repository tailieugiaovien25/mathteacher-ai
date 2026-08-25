from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from assessment_generation_v2.services.exam_generation_service import (
    AssessmentBlueprintSelection,
    AssessmentBlueprintUnavailableError,
    AssessmentDraftIdentity,
    AssessmentExamGenerationRequest,
    AssessmentExamGenerationService,
    AssessmentGenerationValidationError,
    AssessmentValidationReport,
    ExamGenerationState,
)


OWNER_ID = "11111111-1111-4111-8111-111111111111"
BLUEPRINT_VERSION_ID = (
    "22222222-2222-4222-8222-222222222222"
)
EXAM_ID = "33333333-3333-4333-8333-333333333333"
EXAM_VERSION_ID = (
    "44444444-4444-4444-8444-444444444444"
)
VARIANT_IDS = (
    "55555555-5555-4555-8555-555555555551",
    "55555555-5555-4555-8555-555555555552",
)


class FakeAssessmentGenerationGateway:
    def __init__(
        self,
        *,
        report: AssessmentValidationReport | None = None,
        blueprint: AssessmentBlueprintSelection | None = None,
        variant_ids: tuple[str, ...] = VARIANT_IDS,
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
        self.variant_ids = variant_ids
        self.calls: list[str] = []

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
    ) -> AssessmentValidationReport:
        self.calls.append("validate")
        return self.report

    def create_exam_variants(
        self,
        *,
        exam_version_id: str,
        variant_count: int,
    ) -> tuple[str, ...]:
        self.calls.append("create_variants")
        return self.variant_ids[:variant_count]

    def submit_exam_for_review(
        self,
        *,
        exam_version_id: str,
    ) -> None:
        self.calls.append("submit_review")


def _request(
    *,
    submit_for_review: bool = True,
    variant_count: int = 2,
) -> AssessmentExamGenerationRequest:
    return AssessmentExamGenerationRequest(
        blueprint_code="TOAN6_GIUA_HK1",
        owner_user_id=OWNER_ID,
        exam_code="KT_GHK1_TOAN6_001",
        title="Kiểm tra giữa học kỳ I môn Toán 6",
        variant_count=variant_count,
        submit_for_review=submit_for_review,
        idempotency_key="teacher-1-toan6-ghk1-001",
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
        "create_variants",
        "submit_review",
    ]
    assert result.state is ExamGenerationState.PENDING_REVIEW
    assert result.variant_ids == VARIANT_IDS
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
    assert result.variant_ids == ()
    assert "create_variants" not in gateway.calls
    assert "submit_review" not in gateway.calls


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
            title="Đề kiểm tra",
            idempotency_key="request-1",
        )


@pytest.mark.parametrize("variant_count", (0, 25))
def test_variant_count_is_bounded(
    variant_count: int,
) -> None:
    with pytest.raises(
        AssessmentGenerationValidationError
    ):
        _request(variant_count=variant_count)


def test_gateway_must_return_requested_variant_count() -> None:
    gateway = FakeAssessmentGenerationGateway(
        variant_ids=(VARIANT_IDS[0],)
    )
    service = AssessmentExamGenerationService(
        gateway=gateway
    )

    with pytest.raises(
        RuntimeError,
        match="unexpected number of variants",
    ):
        service.generate(request=_request(variant_count=2))


@pytest.mark.parametrize(
    ("variant_ids", "message"),
    (
        (
            [
                VARIANT_IDS[0],
                VARIANT_IDS[1],
            ],
            "tuple",
        ),
        (
            (
                VARIANT_IDS[0],
                VARIANT_IDS[0],
            ),
            "duplicate",
        ),
        (
            (
                VARIANT_IDS[0],
                "not-a-uuid",
            ),
            "invalid",
        ),
    ),
)
def test_invalid_gateway_variants_stop_before_submission(
    variant_ids: object,
    message: str,
) -> None:
    gateway = FakeAssessmentGenerationGateway()
    gateway.variant_ids = variant_ids
    service = AssessmentExamGenerationService(
        gateway=gateway
    )

    with pytest.raises(RuntimeError, match=message):
        service.generate(request=_request())

    assert "submit_review" not in gateway.calls


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
