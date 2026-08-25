from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Protocol
from uuid import UUID


class AssessmentGenerationValidationError(ValueError):
    """Raised when an exam-generation request is invalid."""


class AssessmentBlueprintUnavailableError(LookupError):
    """Raised when no approved active blueprint can be used."""


class ExamGenerationState(str, Enum):
    DRAFT = "DRAFT"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    PENDING_REVIEW = "PENDING_REVIEW"


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise AssessmentGenerationValidationError(
            f"{field_name} must not be blank"
        )

    return normalized


def _required_uuid(value: object, field_name: str) -> str:
    normalized = _required_text(value, field_name)

    try:
        UUID(normalized)
    except ValueError as error:
        raise AssessmentGenerationValidationError(
            f"{field_name} must be a valid UUID"
        ) from error

    return normalized


@dataclass(frozen=True)
class AssessmentExamGenerationRequest:
    blueprint_code: str
    owner_user_id: str
    exam_code: str
    title: str
    variant_count: int = 1
    submit_for_review: bool = True
    idempotency_key: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "blueprint_code",
            _required_text(
                self.blueprint_code,
                "blueprint_code",
            ),
        )
        object.__setattr__(
            self,
            "owner_user_id",
            _required_uuid(
                self.owner_user_id,
                "owner_user_id",
            ),
        )
        object.__setattr__(
            self,
            "exam_code",
            _required_text(
                self.exam_code,
                "exam_code",
            ),
        )
        object.__setattr__(
            self,
            "title",
            _required_text(
                self.title,
                "title",
            ),
        )
        object.__setattr__(
            self,
            "idempotency_key",
            _required_text(
                self.idempotency_key,
                "idempotency_key",
            ),
        )

        if isinstance(self.variant_count, bool):
            raise TypeError(
                "variant_count must be an integer"
            )
        if not isinstance(self.variant_count, int):
            raise TypeError(
                "variant_count must be an integer"
            )
        if self.variant_count < 1:
            raise AssessmentGenerationValidationError(
                "variant_count must be at least 1"
            )
        if self.variant_count > 24:
            raise AssessmentGenerationValidationError(
                "variant_count must not exceed 24"
            )
        if not isinstance(self.submit_for_review, bool):
            raise TypeError(
                "submit_for_review must be a boolean"
            )


@dataclass(frozen=True)
class AssessmentValidationReport:
    is_valid: bool
    violations: tuple[str, ...] = ()
    metrics: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.is_valid, bool):
            raise TypeError("is_valid must be a boolean")
        if not isinstance(self.violations, tuple):
            raise TypeError("violations must be a tuple")
        if any(
            not isinstance(item, str) or not item.strip()
            for item in self.violations
        ):
            raise AssessmentGenerationValidationError(
                "violations must contain non-blank strings"
            )
        if self.is_valid and self.violations:
            raise AssessmentGenerationValidationError(
                "a valid report must not contain violations"
            )
        if not self.is_valid and not self.violations:
            raise AssessmentGenerationValidationError(
                "an invalid report must contain violations"
            )

        source_metrics = (
            {}
            if self.metrics is None
            else dict(self.metrics)
        )
        object.__setattr__(
            self,
            "metrics",
            MappingProxyType(source_metrics),
        )


@dataclass(frozen=True)
class AssessmentExamGenerationResult:
    exam_id: str
    exam_version_id: str
    blueprint_version_id: str
    state: ExamGenerationState
    validation_report: AssessmentValidationReport
    variant_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "exam_id",
            _required_uuid(self.exam_id, "exam_id"),
        )
        object.__setattr__(
            self,
            "exam_version_id",
            _required_uuid(
                self.exam_version_id,
                "exam_version_id",
            ),
        )
        object.__setattr__(
            self,
            "blueprint_version_id",
            _required_uuid(
                self.blueprint_version_id,
                "blueprint_version_id",
            ),
        )
        if not isinstance(self.state, ExamGenerationState):
            raise TypeError(
                "state must be ExamGenerationState"
            )
        if not isinstance(
            self.validation_report,
            AssessmentValidationReport,
        ):
            raise TypeError(
                "validation_report must be "
                "AssessmentValidationReport"
            )
        if not isinstance(self.variant_ids, tuple):
            raise TypeError("variant_ids must be a tuple")

        for variant_id in self.variant_ids:
            _required_uuid(variant_id, "variant_id")


@dataclass(frozen=True)
class AssessmentBlueprintSelection:
    blueprint_version_id: str
    blueprint_code: str
    lifecycle_status: str
    review_status: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "blueprint_version_id",
            _required_uuid(
                self.blueprint_version_id,
                "blueprint_version_id",
            ),
        )
        object.__setattr__(
            self,
            "blueprint_code",
            _required_text(
                self.blueprint_code,
                "blueprint_code",
            ),
        )
        object.__setattr__(
            self,
            "lifecycle_status",
            _required_text(
                self.lifecycle_status,
                "lifecycle_status",
            ),
        )
        object.__setattr__(
            self,
            "review_status",
            _required_text(
                self.review_status,
                "review_status",
            ),
        )


@dataclass(frozen=True)
class AssessmentDraftIdentity:
    exam_id: str
    exam_version_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "exam_id",
            _required_uuid(self.exam_id, "exam_id"),
        )
        object.__setattr__(
            self,
            "exam_version_id",
            _required_uuid(
                self.exam_version_id,
                "exam_version_id",
            ),
        )


class AssessmentExamGenerationGateway(Protocol):
    """
    Persistence boundary used by the application service.

    Implementations may use database functions, a local adapter,
    or a deterministic in-memory test double.
    """

    def find_active_approved_blueprint(
        self,
        *,
        blueprint_code: str,
    ) -> AssessmentBlueprintSelection | None:
        ...

    def create_exam_draft(
        self,
        *,
        request: AssessmentExamGenerationRequest,
        blueprint_version_id: str,
    ) -> AssessmentDraftIdentity:
        ...

    def assemble_exam_version(
        self,
        *,
        exam_version_id: str,
        blueprint_version_id: str,
    ) -> None:
        ...

    def validate_exam_version(
        self,
        *,
        exam_version_id: str,
    ) -> AssessmentValidationReport:
        ...

    def create_exam_variants(
        self,
        *,
        exam_version_id: str,
        variant_count: int,
    ) -> tuple[str, ...]:
        ...

    def submit_exam_for_review(
        self,
        *,
        exam_version_id: str,
    ) -> None:
        ...


class AssessmentExamGenerationService:
    """
    Coordinate deterministic exam generation.

    This service does not approve, publish, or export an exam.
    Those operations remain explicit human-governed workflows.
    """

    def __init__(
        self,
        *,
        gateway: AssessmentExamGenerationGateway,
    ) -> None:
        if gateway is None:
            raise ValueError("gateway must not be None")

        self._gateway = gateway

    def generate(
        self,
        *,
        request: AssessmentExamGenerationRequest,
    ) -> AssessmentExamGenerationResult:
        if not isinstance(
            request,
            AssessmentExamGenerationRequest,
        ):
            raise TypeError(
                "request must be "
                "AssessmentExamGenerationRequest"
            )

        blueprint = (
            self._gateway.find_active_approved_blueprint(
                blueprint_code=request.blueprint_code,
            )
        )

        if blueprint is None:
            raise AssessmentBlueprintUnavailableError(
                "no active approved blueprint is available"
            )

        if blueprint.blueprint_code != request.blueprint_code:
            raise AssessmentBlueprintUnavailableError(
                "gateway returned a different blueprint"
            )

        if blueprint.lifecycle_status != "ACTIVE":
            raise AssessmentBlueprintUnavailableError(
                "blueprint must be active"
            )

        if blueprint.review_status != "APPROVED":
            raise AssessmentBlueprintUnavailableError(
                "blueprint version must be approved"
            )

        draft = self._gateway.create_exam_draft(
            request=request,
            blueprint_version_id=(
                blueprint.blueprint_version_id
            ),
        )

        self._gateway.assemble_exam_version(
            exam_version_id=draft.exam_version_id,
            blueprint_version_id=(
                blueprint.blueprint_version_id
            ),
        )

        report = self._gateway.validate_exam_version(
            exam_version_id=draft.exam_version_id,
        )

        if not report.is_valid:
            return AssessmentExamGenerationResult(
                exam_id=draft.exam_id,
                exam_version_id=draft.exam_version_id,
                blueprint_version_id=(
                    blueprint.blueprint_version_id
                ),
                state=(
                    ExamGenerationState.REVISION_REQUIRED
                ),
                validation_report=report,
            )

        variant_ids = self._gateway.create_exam_variants(
            exam_version_id=draft.exam_version_id,
            variant_count=request.variant_count,
        )

        if not isinstance(variant_ids, tuple):
            raise RuntimeError(
                "gateway must return variants as a tuple"
            )

        if len(variant_ids) != request.variant_count:
            raise RuntimeError(
                "gateway returned an unexpected "
                "number of variants"
            )

        if len(set(variant_ids)) != len(variant_ids):
            raise RuntimeError(
                "gateway returned duplicate variant identifiers"
            )

        for variant_id in variant_ids:
            try:
                _required_uuid(
                    variant_id,
                    "variant_id",
                )
            except (
                TypeError,
                AssessmentGenerationValidationError,
            ) as error:
                raise RuntimeError(
                    "gateway returned an invalid "
                    "variant identifier"
                ) from error

        state = ExamGenerationState.READY_FOR_REVIEW

        if request.submit_for_review:
            self._gateway.submit_exam_for_review(
                exam_version_id=draft.exam_version_id,
            )
            state = ExamGenerationState.PENDING_REVIEW

        return AssessmentExamGenerationResult(
            exam_id=draft.exam_id,
            exam_version_id=draft.exam_version_id,
            blueprint_version_id=(
                blueprint.blueprint_version_id
            ),
            state=state,
            validation_report=report,
            variant_ids=variant_ids,
        )
