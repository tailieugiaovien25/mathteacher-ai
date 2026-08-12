from datetime import date

from src.core_v2.validation import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    Validator,
)

from src.curriculum_v2.models import (
    LearningOutcome,
)


class LearningOutcomeValidator(Validator):

    @property
    def data_type_id(self) -> str:
        return "LEARNING_OUTCOME"

    def validate(
        self,
        data,
    ) -> ValidationResult:

        if not isinstance(
            data,
            LearningOutcome,
        ):
            return ValidationResult.from_issues(
                ValidationIssue(
                    code="LO_INVALID_TYPE",
                    message=(
                        "Dữ liệu phải là "
                        "LearningOutcome."
                    ),
                    severity=(
                        ValidationSeverity.ERROR
                    ),
                )
            )

        issues = []

        required_fields = (
            (
                "learning_outcome_id",
                data.learning_outcome_id,
            ),
            (
                "curriculum_ref",
                data.curriculum_ref,
            ),
            (
                "code",
                data.code,
            ),
            (
                "statement",
                data.statement,
            ),
            (
                "outcome_type",
                data.outcome_type,
            ),
            (
                "status",
                data.status,
            ),
        )

        for field_name, value in required_fields:

            if not (
                isinstance(value, str)
                and value.strip()
            ):
                issues.append(
                    ValidationIssue(
                        code="LO_REQUIRED_FIELD",
                        message=(
                            f"{field_name} "
                            "không được để trống."
                        ),
                        severity=(
                            ValidationSeverity.ERROR
                        ),
                        field=field_name,
                    )
                )

        effective_from = self._parse_date(
            data.effective_from,
            field_name="effective_from",
            issues=issues,
        )

        effective_to = self._parse_date(
            data.effective_to,
            field_name="effective_to",
            issues=issues,
        )

        if (
            effective_from is not None
            and effective_to is not None
            and effective_to < effective_from
        ):
            issues.append(
                ValidationIssue(
                    code="LO_INVALID_EFFECTIVE_PERIOD",
                    message=(
                        "effective_to không được "
                        "trước effective_from."
                    ),
                    severity=(
                        ValidationSeverity.ERROR
                    ),
                    field="effective_to",
                )
            )

        if issues:
            return ValidationResult(
                issues=tuple(issues)
            )

        return ValidationResult.pass_result()

    @staticmethod
    def _parse_date(
        value,
        *,
        field_name: str,
        issues: list,
    ):

        if value is None:
            return None

        if not isinstance(value, str):
            issues.append(
                ValidationIssue(
                    code="LO_INVALID_DATE",
                    message=(
                        f"{field_name} phải có "
                        "định dạng YYYY-MM-DD."
                    ),
                    severity=(
                        ValidationSeverity.ERROR
                    ),
                    field=field_name,
                )
            )
            return None

        try:
            return date.fromisoformat(value)

        except ValueError:
            issues.append(
                ValidationIssue(
                    code="LO_INVALID_DATE",
                    message=(
                        f"{field_name} phải có "
                        "định dạng YYYY-MM-DD."
                    ),
                    severity=(
                        ValidationSeverity.ERROR
                    ),
                    field=field_name,
                )
            )
            return None