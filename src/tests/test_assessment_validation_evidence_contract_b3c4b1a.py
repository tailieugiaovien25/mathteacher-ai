from __future__ import annotations

from datetime import datetime, timezone

import pytest

from assessment_generation_v2.services.assessment_foundation import (
    AssessmentFoundationError,
    ValidationEvidenceIdentity,
    ValidationResult,
    ValidationSemanticsLossError,
    ValidationStatus,
    validation_result_from_legacy,
    validation_result_to_legacy,
)
from assessment_generation_v2.services.exam_generation_service import (
    AssessmentValidationReport,
)


EVIDENCE_ID = "11111111-1111-4111-8111-111111111111"
VALIDATION_INPUT_DIGEST = "a" * 64
EVIDENCE_DIGEST = "b" * 64
VALIDATED_AT = datetime(2026, 9, 13, 8, 30, tzinfo=timezone.utc)


def _evidence_identity(**overrides: object) -> ValidationEvidenceIdentity:
    values: dict[str, object] = {
        "validation_evidence_id": EVIDENCE_ID,
        "validation_input_digest": VALIDATION_INPUT_DIGEST,
        "evidence_digest": EVIDENCE_DIGEST,
        "validation_schema_version": 1,
        "validated_at": VALIDATED_AT,
    }
    values.update(overrides)
    return ValidationEvidenceIdentity(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("result", "expected_status"),
    (
        (ValidationResult(status=ValidationStatus.PASS), ValidationStatus.PASS),
        (
            ValidationResult(
                status=ValidationStatus.WARNING,
                warnings=("Teacher review required.",),
            ),
            ValidationStatus.WARNING,
        ),
        (
            ValidationResult(
                status=ValidationStatus.FAIL,
                errors=("Validation failed.",),
            ),
            ValidationStatus.FAIL,
        ),
    ),
)
def test_existing_validation_result_constructors_remain_valid(
    result: ValidationResult,
    expected_status: ValidationStatus,
) -> None:
    assert result.status is expected_status
    assert result.evidence_identity is None


@pytest.mark.parametrize(
    ("legacy", "expected_status"),
    (
        (AssessmentValidationReport(is_valid=True), ValidationStatus.PASS),
        (
            AssessmentValidationReport(
                is_valid=False,
                violations=("Validation failed.",),
            ),
            ValidationStatus.FAIL,
        ),
    ),
)
def test_legacy_conversion_remains_pass_or_fail_only(
    legacy: AssessmentValidationReport,
    expected_status: ValidationStatus,
) -> None:
    result = validation_result_from_legacy(legacy)

    assert result.status is expected_status
    assert result.evidence_identity is None


def test_warning_to_legacy_still_rejects_semantics_loss() -> None:
    result = ValidationResult(
        status=ValidationStatus.WARNING,
        warnings=("Teacher review required.",),
    )

    with pytest.raises(ValidationSemanticsLossError):
        validation_result_to_legacy(result)


@pytest.mark.parametrize(
    ("result", "expected_valid", "expected_violations"),
    (
        (ValidationResult(status=ValidationStatus.PASS), True, ()),
        (
            ValidationResult(
                status=ValidationStatus.FAIL,
                errors=("Validation failed.",),
            ),
            False,
            ("Validation failed.",),
        ),
    ),
)
def test_pass_and_fail_conversion_to_legacy_remains_exact(
    result: ValidationResult,
    expected_valid: bool,
    expected_violations: tuple[str, ...],
) -> None:
    legacy = validation_result_to_legacy(result)

    assert legacy.is_valid is expected_valid
    assert legacy.violations == expected_violations


def test_complete_persisted_evidence_identity_is_accepted_and_preserved() -> None:
    identity = _evidence_identity()
    result = ValidationResult(
        status=ValidationStatus.PASS,
        evidence_identity=identity,
    )

    assert result.evidence_identity is identity
    assert identity.validation_evidence_id == EVIDENCE_ID
    assert identity.validation_input_digest == VALIDATION_INPUT_DIGEST
    assert identity.evidence_digest == EVIDENCE_DIGEST
    assert identity.validation_schema_version == 1
    assert identity.validated_at is VALIDATED_AT


def test_evidence_identity_preserves_warning_status_and_warning_order() -> None:
    warnings = (
        "First canonical warning.",
        "Second canonical warning.",
    )

    result = ValidationResult(
        status=ValidationStatus.WARNING,
        warnings=warnings,
        evidence_identity=_evidence_identity(),
    )

    assert result.status is ValidationStatus.WARNING
    assert result.warnings == warnings


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("evidence_digest", "A" * 64),
        ("evidence_digest", "b" * 63),
        ("validation_input_digest", "g" * 64),
        ("validation_input_digest", "a" * 65),
    ),
)
def test_invalid_digests_are_rejected(
    field_name: str,
    invalid_value: object,
) -> None:
    with pytest.raises(AssessmentFoundationError):
        _evidence_identity(**{field_name: invalid_value})


@pytest.mark.parametrize("invalid_value", (0, -1))
def test_non_positive_schema_versions_are_rejected(invalid_value: int) -> None:
    with pytest.raises(AssessmentFoundationError):
        _evidence_identity(validation_schema_version=invalid_value)


def test_boolean_schema_version_is_rejected() -> None:
    with pytest.raises(TypeError):
        _evidence_identity(validation_schema_version=True)


def test_invalid_evidence_uuid_is_rejected() -> None:
    with pytest.raises(AssessmentFoundationError):
        _evidence_identity(validation_evidence_id="not-a-uuid")


@pytest.mark.parametrize(
    "missing_field",
    (
        "validation_evidence_id",
        "validation_input_digest",
        "evidence_digest",
        "validation_schema_version",
        "validated_at",
    ),
)
def test_partial_evidence_identity_cannot_be_constructed(
    missing_field: str,
) -> None:
    values = {
        "validation_evidence_id": EVIDENCE_ID,
        "validation_input_digest": VALIDATION_INPUT_DIGEST,
        "evidence_digest": EVIDENCE_DIGEST,
        "validation_schema_version": 1,
        "validated_at": VALIDATED_AT,
    }
    del values[missing_field]

    with pytest.raises(TypeError):
        ValidationEvidenceIdentity(**values)  # type: ignore[arg-type]


def test_validation_result_rejects_non_identity_evidence_metadata() -> None:
    with pytest.raises(TypeError):
        ValidationResult(
            status=ValidationStatus.PASS,
            evidence_identity={"validation_evidence_id": EVIDENCE_ID},  # type: ignore[arg-type]
        )


def test_naive_validation_timestamp_is_rejected() -> None:
    with pytest.raises(AssessmentFoundationError):
        _evidence_identity(validated_at=datetime(2026, 9, 13, 8, 30))
