"""Grade-agnostic canonical contracts for assessment generation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Mapping

from assessment_generation_v2.services.assessment_curriculum_query_service import (
    AssessmentLearningRequirement,
)
from assessment_generation_v2.services.assessment_matrix_cell_authoring import (
    AssessmentMatrixCell,
    AssessmentProfileSectionOption,
    CognitiveLevelOption,
    ProfileLevelAllocation,
)
from assessment_generation_v2.services.blueprint_requirement_link_service import (
    BlueprintRequirementAssignment,
)
from assessment_generation_v2.services.canonical_assessment_selection_service import (
    CanonicalAssessmentSelection,
)
from assessment_generation_v2.services.exam_generation_service import (
    AssessmentValidationReport,
)


AssessmentScope = CanonicalAssessmentSelection
CognitiveAllocation = ProfileLevelAllocation
MatrixCell = AssessmentMatrixCell
CompetencyRequirement = AssessmentLearningRequirement


class AssessmentFoundationError(ValueError):
    """Raised when canonical assessment contracts are inconsistent."""


class MathAssessmentPolicyError(AssessmentFoundationError):
    """Raised when a canonical config is outside the Math application policy."""


class ValidationSemanticsLossError(AssessmentFoundationError):
    """Raised when legacy conversion would lose canonical validation meaning."""


def _text(value: object, field_name: str, *, upper: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise AssessmentFoundationError(f"{field_name} must not be blank")
    return normalized.upper() if upper else normalized


def _positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 1:
        raise AssessmentFoundationError(f"{field_name} must be positive")
    return value


def _grade(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("grade_level must be an integer")
    if not 1 <= value <= 12:
        raise AssessmentFoundationError(
            "grade_level must be between 1 and 12"
        )
    return value


def _positive_decimal(value: object, field_name: str) -> Decimal:
    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise AssessmentFoundationError(
            f"{field_name} must be a valid number"
        ) from error
    if not normalized.is_finite() or normalized <= 0:
        raise AssessmentFoundationError(f"{field_name} must be positive")
    return normalized


def _string_tuple(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    normalized = tuple(_text(value, field_name) for value in values)
    if not normalized:
        raise AssessmentFoundationError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise AssessmentFoundationError(f"{field_name} must be unique")
    return tuple(sorted(normalized))


@dataclass(frozen=True, slots=True)
class AssessmentConfig:
    config_code: str
    title: str
    subject_code: str
    grade_level: int
    academic_year: str
    semester: str
    test_type: str
    duration_minutes: int
    total_score: Decimal
    variant_count: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "config_code", _text(self.config_code, "config_code", upper=True)
        )
        object.__setattr__(self, "title", _text(self.title, "title"))
        object.__setattr__(
            self, "subject_code", _text(self.subject_code, "subject_code", upper=True)
        )
        object.__setattr__(self, "grade_level", _grade(self.grade_level))
        object.__setattr__(
            self, "academic_year", _text(self.academic_year, "academic_year")
        )
        object.__setattr__(
            self, "semester", _text(self.semester, "semester", upper=True)
        )
        object.__setattr__(
            self, "test_type", _text(self.test_type, "test_type", upper=True)
        )
        object.__setattr__(
            self,
            "duration_minutes",
            _positive_int(self.duration_minutes, "duration_minutes"),
        )
        object.__setattr__(
            self, "total_score", _positive_decimal(self.total_score, "total_score")
        )
        object.__setattr__(
            self, "variant_count", _positive_int(self.variant_count, "variant_count")
        )


def validate_math_application_grade(grade_level: object) -> int:
    """Apply the current Math 6-9 policy after domain validation."""

    normalized = _grade(grade_level)
    if not 6 <= normalized <= 9:
        raise MathAssessmentPolicyError(
            "Math assessment application supports grades 6 through 9"
        )
    return normalized


def validate_math_assessment_config(config: AssessmentConfig) -> AssessmentConfig:
    if not isinstance(config, AssessmentConfig):
        raise TypeError("config must be AssessmentConfig")
    if config.subject_code != "MATH":
        raise MathAssessmentPolicyError("subject_code must be MATH")
    validate_math_application_grade(config.grade_level)
    return config


validate_math_application_policy = validate_math_assessment_config


@dataclass(frozen=True, slots=True)
class AssessmentStructure:
    sections: tuple[AssessmentProfileSectionOption, ...]

    def __post_init__(self) -> None:
        rows = tuple(self.sections)
        if not rows:
            raise AssessmentFoundationError("sections must not be empty")
        if any(not isinstance(row, AssessmentProfileSectionOption) for row in rows):
            raise TypeError("sections must contain AssessmentProfileSectionOption")
        codes = tuple(row.section_code for row in rows)
        sequences = tuple(row.sequence_number for row in rows)
        if len(set(codes)) != len(codes):
            raise AssessmentFoundationError("section codes must be unique")
        if len(set(sequences)) != len(sequences):
            raise AssessmentFoundationError("section sequences must be unique")
        object.__setattr__(
            self,
            "sections",
            tuple(sorted(rows, key=lambda row: (row.sequence_number, row.section_code))),
        )

    @property
    def question_count(self) -> int:
        return sum(row.question_count for row in self.sections)

    @property
    def response_count(self) -> int:
        return sum(row.response_count for row in self.sections)

    @property
    def total_score(self) -> Decimal:
        return sum((row.section_score for row in self.sections), Decimal("0"))


@dataclass(frozen=True, slots=True)
class QuestionRequirement:
    question_requirement_code: str
    matrix_cell_sequence_number: int
    competency_requirement_codes: tuple[str, ...]
    question_count: int
    response_count: int
    target_score: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "question_requirement_code",
            _text(
                self.question_requirement_code,
                "question_requirement_code",
                upper=True,
            ),
        )
        object.__setattr__(
            self,
            "matrix_cell_sequence_number",
            _positive_int(
                self.matrix_cell_sequence_number,
                "matrix_cell_sequence_number",
            ),
        )
        object.__setattr__(
            self,
            "competency_requirement_codes",
            _string_tuple(
                self.competency_requirement_codes,
                "competency_requirement_codes",
            ),
        )
        object.__setattr__(
            self, "question_count", _positive_int(self.question_count, "question_count")
        )
        object.__setattr__(
            self, "response_count", _positive_int(self.response_count, "response_count")
        )
        object.__setattr__(
            self, "target_score", _positive_decimal(self.target_score, "target_score")
        )


@dataclass(frozen=True, slots=True)
class AssessmentSpecification:
    specification_code: str
    title: str
    config: AssessmentConfig
    scope: AssessmentScope
    structure: AssessmentStructure
    cognitive_allocations: tuple[CognitiveAllocation, ...]
    competency_requirements: tuple[CompetencyRequirement, ...]
    requirement_assignments: tuple[BlueprintRequirementAssignment, ...]
    matrix_cells: tuple[MatrixCell, ...]
    question_requirements: tuple[QuestionRequirement, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "specification_code",
            _text(self.specification_code, "specification_code", upper=True),
        )
        object.__setattr__(self, "title", _text(self.title, "title"))
        if self.schema_version != 1:
            raise AssessmentFoundationError("schema_version must be 1")
        if not isinstance(self.config, AssessmentConfig):
            raise TypeError("config must be AssessmentConfig")
        if not isinstance(self.scope, CanonicalAssessmentSelection):
            raise TypeError("scope must be CanonicalAssessmentSelection")
        if not isinstance(self.structure, AssessmentStructure):
            raise TypeError("structure must be AssessmentStructure")

        allocations = tuple(self.cognitive_allocations)
        requirements = tuple(self.competency_requirements)
        assignments = tuple(self.requirement_assignments)
        cells = tuple(self.matrix_cells)
        question_requirements = tuple(self.question_requirements)
        self._validate_row_types(
            allocations, requirements, assignments, cells, question_requirements
        )

        allocations = tuple(sorted(allocations, key=lambda row: row.cognitive_level_code))
        requirements = tuple(sorted(requirements, key=lambda row: row.requirement_code))
        assignments = tuple(
            sorted(assignments, key=lambda row: (row.sequence_number, row.requirement_code))
        )
        cells = tuple(sorted(cells, key=lambda row: row.sequence_number))
        question_requirements = tuple(
            sorted(
                question_requirements,
                key=lambda row: (
                    row.matrix_cell_sequence_number,
                    row.question_requirement_code,
                ),
            )
        )
        object.__setattr__(self, "cognitive_allocations", allocations)
        object.__setattr__(self, "competency_requirements", requirements)
        object.__setattr__(self, "requirement_assignments", assignments)
        object.__setattr__(self, "matrix_cells", cells)
        object.__setattr__(self, "question_requirements", question_requirements)
        self._validate_consistency()

    @staticmethod
    def _validate_row_types(
        allocations: tuple[CognitiveAllocation, ...],
        requirements: tuple[CompetencyRequirement, ...],
        assignments: tuple[BlueprintRequirementAssignment, ...],
        cells: tuple[MatrixCell, ...],
        question_requirements: tuple[QuestionRequirement, ...],
    ) -> None:
        expected = (
            (allocations, ProfileLevelAllocation, "cognitive_allocations"),
            (requirements, AssessmentLearningRequirement, "competency_requirements"),
            (assignments, BlueprintRequirementAssignment, "requirement_assignments"),
            (cells, AssessmentMatrixCell, "matrix_cells"),
            (question_requirements, QuestionRequirement, "question_requirements"),
        )
        for rows, row_type, field_name in expected:
            if not rows:
                raise AssessmentFoundationError(f"{field_name} must not be empty")
            if any(not isinstance(row, row_type) for row in rows):
                raise TypeError(f"{field_name} contains an invalid value")

    def _validate_consistency(self) -> None:
        if not self.scope.finalized:
            raise AssessmentFoundationError("scope must be finalized")
        if self.config.subject_code != self.scope.subject_code.upper():
            raise AssessmentFoundationError("config subject does not match scope")
        if self.config.grade_level != self.scope.grade_level:
            raise AssessmentFoundationError("config grade does not match scope")
        if self.structure.total_score != self.config.total_score:
            raise AssessmentFoundationError("structure score does not match config")

        requirement_codes = tuple(
            row.requirement_code for row in self.competency_requirements
        )
        if len(set(requirement_codes)) != len(requirement_codes):
            raise AssessmentFoundationError("competency requirement codes must be unique")
        if set(requirement_codes) != set(self.scope.selected_requirement_codes):
            raise AssessmentFoundationError(
                "competency requirements must match selected canonical requirements"
            )
        selected_topics = set(self.scope.selected_topic_codes)
        for requirement in self.competency_requirements:
            if (
                requirement.program_code != self.scope.program_code
                or requirement.grade_level != self.scope.grade_level
                or requirement.topic_code not in selected_topics
            ):
                raise AssessmentFoundationError(
                    "competency requirement evidence does not match scope"
                )

        assignment_codes = tuple(
            row.requirement_code for row in self.requirement_assignments
        )
        if len(set(assignment_codes)) != len(assignment_codes):
            raise AssessmentFoundationError("assignment requirement codes must be unique")
        if set(assignment_codes) != set(requirement_codes):
            raise AssessmentFoundationError(
                "assignment requirement codes must match canonical requirements"
            )

        allocation_codes = tuple(
            row.cognitive_level_code for row in self.cognitive_allocations
        )
        if len(set(allocation_codes)) != len(allocation_codes):
            raise AssessmentFoundationError("cognitive allocation codes must be unique")
        if sum(
            (row.target_score for row in self.cognitive_allocations), Decimal("0")
        ) != self.config.total_score:
            raise AssessmentFoundationError("cognitive allocation score must match config")

        section_codes = {row.section_code for row in self.structure.sections}
        cell_sequences = tuple(row.sequence_number for row in self.matrix_cells)
        if len(set(cell_sequences)) != len(cell_sequences):
            raise AssessmentFoundationError("matrix cell sequences must be unique")
        for cell in self.matrix_cells:
            if cell.section_code not in section_codes:
                raise AssessmentFoundationError("matrix cell references unknown section")
            if cell.topic_code not in selected_topics:
                raise AssessmentFoundationError("matrix cell references unknown topic")
            if cell.cognitive_level_code not in set(allocation_codes):
                raise AssessmentFoundationError(
                    "matrix cell references unknown cognitive allocation"
                )
        if (
            sum(row.question_count for row in self.matrix_cells)
            != self.structure.question_count
            or sum(row.response_count for row in self.matrix_cells)
            != self.structure.response_count
            or sum((row.target_score for row in self.matrix_cells), Decimal("0"))
            != self.structure.total_score
        ):
            raise AssessmentFoundationError("matrix totals do not match structure")

        question_codes = tuple(
            row.question_requirement_code for row in self.question_requirements
        )
        if len(set(question_codes)) != len(question_codes):
            raise AssessmentFoundationError("question requirement codes must be unique")
        canonical_codes = set(requirement_codes)
        by_cell: dict[int, list[QuestionRequirement]] = {}
        for row in self.question_requirements:
            if not set(row.competency_requirement_codes) <= canonical_codes:
                raise AssessmentFoundationError(
                    "question requirement references unknown canonical requirement"
                )
            by_cell.setdefault(row.matrix_cell_sequence_number, []).append(row)
        if set(by_cell) != set(cell_sequences):
            raise AssessmentFoundationError(
                "question requirements must partition every matrix cell"
            )
        for cell in self.matrix_cells:
            rows = by_cell[cell.sequence_number]
            if (
                sum(row.question_count for row in rows) != cell.question_count
                or sum(row.response_count for row in rows) != cell.response_count
                or sum((row.target_score for row in rows), Decimal("0"))
                != cell.target_score
            ):
                raise AssessmentFoundationError(
                    "question requirements must exactly partition matrix cells"
                )


class ValidationStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class ValidationResult:
    status: ValidationStatus
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    metrics: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, ValidationStatus):
            raise TypeError("status must be ValidationStatus")
        errors = self._messages(self.errors, "errors")
        warnings = self._messages(self.warnings, "warnings")
        if self.status is ValidationStatus.PASS and (errors or warnings):
            raise AssessmentFoundationError("PASS cannot contain errors or warnings")
        if self.status is ValidationStatus.WARNING and (errors or not warnings):
            raise AssessmentFoundationError(
                "WARNING requires warnings and cannot contain errors"
            )
        if self.status is ValidationStatus.FAIL and not errors:
            raise AssessmentFoundationError("FAIL requires errors")
        object.__setattr__(self, "errors", errors)
        object.__setattr__(self, "warnings", warnings)
        object.__setattr__(
            self,
            "metrics",
            MappingProxyType({} if self.metrics is None else dict(self.metrics)),
        )

    @staticmethod
    def _messages(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
        if not isinstance(values, tuple):
            raise TypeError(f"{field_name} must be a tuple")
        normalized = tuple(_text(value, field_name) for value in values)
        return normalized

    @property
    def may_continue_automatically(self) -> bool:
        return self.status is ValidationStatus.PASS

    @property
    def requires_teacher_confirmation(self) -> bool:
        return self.status is ValidationStatus.WARNING

    @property
    def blocked(self) -> bool:
        return self.status is ValidationStatus.FAIL

    @classmethod
    def from_legacy(cls, report: AssessmentValidationReport) -> "ValidationResult":
        return validation_result_from_legacy(report)

    def to_legacy(self) -> AssessmentValidationReport:
        return validation_result_to_legacy(self)


def validation_result_from_legacy(
    report: AssessmentValidationReport,
) -> ValidationResult:
    if not isinstance(report, AssessmentValidationReport):
        raise TypeError("report must be AssessmentValidationReport")
    if report.is_valid:
        return ValidationResult(status=ValidationStatus.PASS, metrics=report.metrics)
    return ValidationResult(
        status=ValidationStatus.FAIL,
        errors=report.violations,
        metrics=report.metrics,
    )


def validation_result_to_legacy(
    result: ValidationResult,
) -> AssessmentValidationReport:
    if not isinstance(result, ValidationResult):
        raise TypeError("result must be ValidationResult")
    if result.status is ValidationStatus.WARNING:
        raise ValidationSemanticsLossError(
            "WARNING cannot be represented by legacy boolean validity"
        )
    violations = result.errors
    if result.warnings:
        violations += tuple(f"WARNING: {warning}" for warning in result.warnings)
    return AssessmentValidationReport(
        is_valid=result.status is ValidationStatus.PASS,
        violations=violations,
        metrics=result.metrics,
    )


from_legacy_validation_report = validation_result_from_legacy
to_legacy_validation_report = validation_result_to_legacy


__all__ = [
    "AssessmentConfig",
    "AssessmentFoundationError",
    "AssessmentScope",
    "AssessmentSpecification",
    "AssessmentStructure",
    "BlueprintRequirementAssignment",
    "CognitiveAllocation",
    "CognitiveLevelOption",
    "CompetencyRequirement",
    "MathAssessmentPolicyError",
    "MatrixCell",
    "QuestionRequirement",
    "ValidationResult",
    "ValidationSemanticsLossError",
    "ValidationStatus",
    "from_legacy_validation_report",
    "to_legacy_validation_report",
    "validate_math_application_grade",
    "validate_math_application_policy",
    "validate_math_assessment_config",
    "validation_result_from_legacy",
    "validation_result_to_legacy",
]
