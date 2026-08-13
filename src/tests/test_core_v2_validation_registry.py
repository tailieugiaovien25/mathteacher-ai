from typing import Any

from src.core_v2.validation import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    Validator,
    ValidatorRegistry,
)


class FakeAcademicUnitValidator(Validator):

    @property
    def data_type_id(self) -> str:
        return "ACADEMIC_UNIT"

    def validate(
        self,
        data: Any,
    ) -> ValidationResult:

        if not isinstance(data, dict):
            return ValidationResult.from_issues(
                ValidationIssue(
                    code="AU_INVALID_DATA",
                    message="Dữ liệu phải là dict.",
                    severity=ValidationSeverity.ERROR,
                )
            )

        if not data.get("academic_unit_id"):
            return ValidationResult.from_issues(
                ValidationIssue(
                    code="AU_ID_REQUIRED",
                    message="academic_unit_id là bắt buộc.",
                    severity=ValidationSeverity.ERROR,
                    field="academic_unit_id",
                )
            )

        return ValidationResult.pass_result()


def main():
    print("=" * 72)
    print(
        "V2-CORE-004B - "
        "VALIDATOR REGISTRY TEST"
    )
    print("=" * 72)

    registry = ValidatorRegistry()

    validator = FakeAcademicUnitValidator()

    registry.register(
        validator
    )

    assert registry.exists(
        "ACADEMIC_UNIT"
    )

    assert (
        registry.get(
            "ACADEMIC_UNIT"
        )
        is validator
    )

    print(
        "Register validator: PASS"
    )

    valid_result = validator.validate(
        {
            "academic_unit_id": "AU-001",
        }
    )

    assert valid_result.is_valid
    assert not valid_result.has_errors

    print(
        "Valid data: PASS"
    )

    invalid_result = validator.validate(
        {}
    )

    assert not invalid_result.is_valid
    assert invalid_result.has_errors

    print(
        "Invalid data blocked: PASS"
    )

    duplicate_blocked = False

    try:
        registry.register(
            FakeAcademicUnitValidator()
        )

    except ValueError:
        duplicate_blocked = True

    assert duplicate_blocked

    print(
        "Duplicate validator blocked: PASS"
    )

    unknown_blocked = False

    try:
        registry.get(
            "UNKNOWN_DATA_TYPE"
        )

    except KeyError:
        unknown_blocked = True

    assert unknown_blocked

    print(
        "Unknown validator blocked: PASS"
    )

    print()

    print(
        "RESULT: "
        "PASS - VALIDATION FOUNDATION VERIFIED"
    )


if __name__ == "__main__":
    main()