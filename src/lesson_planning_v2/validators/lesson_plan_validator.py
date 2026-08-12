from core_v2.validation.validation_result import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)
from core_v2.validation.validator import Validator
from lesson_planning_v2.models import LessonPlan
from lesson_planning_v2.rules import validate_lesson_plan_structure


class LessonPlanValidator(Validator):
    """Validate canonical lesson-plan domain invariants."""

    @property
    def data_type_id(self) -> str:
        return "LESSON_PLAN"

    def validate(self, data: LessonPlan) -> ValidationResult:
        violations = validate_lesson_plan_structure(data)
        issues = tuple(
            ValidationIssue(
                code=violation.code,
                message=violation.message,
                severity=ValidationSeverity.ERROR,
                field=violation.field,
            )
            for violation in violations
        )
        return ValidationResult(issues=issues)
