"""Source-only shared configuration for the Mathematics 6-9 assessment builder.

The service deliberately has no database, Supabase, Streamlit, or publication
dependency. It validates an editing configuration before a later persistence
layer is allowed to use it.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable, Sequence


class AssessmentBuilderConfigurationError(ValueError):
    """Raised when an assessment-builder configuration is inconsistent."""


SUPPORTED_GRADES: tuple[int, ...] = (6, 7, 8, 9)
SUPPORTED_ASSESSMENT_TYPES: tuple[str, ...] = ("REGULAR", "MIDTERM", "FINAL")
SUPPORTED_SEMESTERS: tuple[int, ...] = (1, 2)

QUESTION_TYPE_LABELS: dict[str, str] = {
    "MULTIPLE_CHOICE": "Trắc nghiệm nhiều lựa chọn",
    "TRUE_FALSE": "Trắc nghiệm đúng – sai",
    "SHORT_RESPONSE": "Trả lời ngắn",
    "ESSAY": "Tự luận",
}
COGNITIVE_LEVEL_LABELS: dict[str, str] = {
    "KNOW": "Biết / Nhận biết",
    "UNDERSTAND": "Hiểu / Thông hiểu",
    "APPLY": "Vận dụng",
}


def _decimal(value: object, field_name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise AssessmentBuilderConfigurationError(
            f"{field_name} must be a decimal number"
        ) from error
    if not result.is_finite():
        raise AssessmentBuilderConfigurationError(
            f"{field_name} must be finite"
        )
    return result


def _unique_codes(values: Iterable[object]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        code = str(value or "").strip()
        if not code or code in seen:
            continue
        result.append(code)
        seen.add(code)
    return tuple(result)


@dataclass(frozen=True, slots=True)
class AssessmentBuilderSection:
    section_code: str
    question_type_code: str
    question_count: int
    response_count: int
    section_score: Decimal

    def __post_init__(self) -> None:
        section_code = str(self.section_code or "").strip()
        question_type_code = str(self.question_type_code or "").strip()
        if not section_code:
            raise AssessmentBuilderConfigurationError(
                "section_code is required"
            )
        if question_type_code not in QUESTION_TYPE_LABELS:
            raise AssessmentBuilderConfigurationError(
                f"unsupported question_type_code: {question_type_code}"
            )
        if int(self.question_count) <= 0:
            raise AssessmentBuilderConfigurationError(
                "question_count must be positive"
            )
        if int(self.response_count) < int(self.question_count):
            raise AssessmentBuilderConfigurationError(
                "response_count must be >= question_count"
            )
        section_score = _decimal(self.section_score, "section_score")
        if section_score <= 0:
            raise AssessmentBuilderConfigurationError(
                "section_score must be positive"
            )
        object.__setattr__(self, "section_code", section_code)
        object.__setattr__(self, "question_type_code", question_type_code)
        object.__setattr__(self, "question_count", int(self.question_count))
        object.__setattr__(self, "response_count", int(self.response_count))
        object.__setattr__(self, "section_score", section_score)


@dataclass(frozen=True, slots=True)
class AssessmentBuilderCognitiveAllocation:
    cognitive_level_code: str
    target_percentage: Decimal

    def __post_init__(self) -> None:
        code = str(self.cognitive_level_code or "").strip()
        if code not in COGNITIVE_LEVEL_LABELS:
            raise AssessmentBuilderConfigurationError(
                f"unsupported cognitive_level_code: {code}"
            )
        percentage = _decimal(
            self.target_percentage,
            "target_percentage",
        )
        if percentage < 0 or percentage > 100:
            raise AssessmentBuilderConfigurationError(
                "target_percentage must be between 0 and 100"
            )
        object.__setattr__(self, "cognitive_level_code", code)
        object.__setattr__(self, "target_percentage", percentage)


@dataclass(frozen=True, slots=True)
class AssessmentBuilderConfiguration:
    grade_level: int
    assessment_type_code: str
    semester_number: int
    duration_minutes: int
    total_score: Decimal
    sections: tuple[AssessmentBuilderSection, ...]
    cognitive_allocations: tuple[
        AssessmentBuilderCognitiveAllocation, ...
    ]
    selected_topic_codes: tuple[str, ...] = ()
    selected_requirement_codes: tuple[str, ...] = ()
    subject_code: str = "MATH"

    def __post_init__(self) -> None:
        grade_level = int(self.grade_level)
        assessment_type_code = str(
            self.assessment_type_code or ""
        ).strip().upper()
        semester_number = int(self.semester_number)
        duration_minutes = int(self.duration_minutes)
        total_score = _decimal(self.total_score, "total_score")
        subject_code = str(self.subject_code or "").strip().upper()

        if subject_code != "MATH":
            raise AssessmentBuilderConfigurationError(
                "A1-MATH69-B supports subject_code=MATH only"
            )
        if grade_level not in SUPPORTED_GRADES:
            raise AssessmentBuilderConfigurationError(
                "grade_level must be one of 6, 7, 8, 9"
            )
        if assessment_type_code not in SUPPORTED_ASSESSMENT_TYPES:
            raise AssessmentBuilderConfigurationError(
                "assessment_type_code must be REGULAR, MIDTERM, or FINAL"
            )
        if semester_number not in SUPPORTED_SEMESTERS:
            raise AssessmentBuilderConfigurationError(
                "semester_number must be 1 or 2"
            )
        if duration_minutes <= 0:
            raise AssessmentBuilderConfigurationError(
                "duration_minutes must be positive"
            )
        if total_score <= 0:
            raise AssessmentBuilderConfigurationError(
                "total_score must be positive"
            )

        sections = tuple(self.sections)
        if not sections:
            raise AssessmentBuilderConfigurationError(
                "at least one section is required"
            )
        section_codes = [row.section_code for row in sections]
        if len(section_codes) != len(set(section_codes)):
            raise AssessmentBuilderConfigurationError(
                "section_code values must be unique"
            )
        question_type_codes = [
            row.question_type_code for row in sections
        ]
        if len(question_type_codes) != len(set(question_type_codes)):
            raise AssessmentBuilderConfigurationError(
                "question_type_code values must be unique"
            )

        section_total = sum(
            (row.section_score for row in sections),
            Decimal("0"),
        )
        if section_total != total_score:
            raise AssessmentBuilderConfigurationError(
                "section scores must equal total_score"
            )

        allocations = tuple(self.cognitive_allocations)
        if not allocations:
            raise AssessmentBuilderConfigurationError(
                "cognitive allocations are required"
            )
        allocation_codes = [
            row.cognitive_level_code for row in allocations
        ]
        if len(allocation_codes) != len(set(allocation_codes)):
            raise AssessmentBuilderConfigurationError(
                "cognitive_level_code values must be unique"
            )
        expected_levels = set(COGNITIVE_LEVEL_LABELS)
        if set(allocation_codes) != expected_levels:
            raise AssessmentBuilderConfigurationError(
                "cognitive allocations must contain KNOW, UNDERSTAND, APPLY"
            )
        allocation_total = sum(
            (row.target_percentage for row in allocations),
            Decimal("0"),
        )
        if allocation_total != Decimal("100"):
            raise AssessmentBuilderConfigurationError(
                "cognitive target percentages must equal 100"
            )

        object.__setattr__(self, "grade_level", grade_level)
        object.__setattr__(
            self,
            "assessment_type_code",
            assessment_type_code,
        )
        object.__setattr__(
            self,
            "semester_number",
            semester_number,
        )
        object.__setattr__(
            self,
            "duration_minutes",
            duration_minutes,
        )
        object.__setattr__(self, "total_score", total_score)
        object.__setattr__(self, "sections", sections)
        object.__setattr__(
            self,
            "cognitive_allocations",
            allocations,
        )
        object.__setattr__(
            self,
            "selected_topic_codes",
            _unique_codes(self.selected_topic_codes),
        )
        object.__setattr__(
            self,
            "selected_requirement_codes",
            _unique_codes(self.selected_requirement_codes),
        )
        object.__setattr__(self, "subject_code", subject_code)


class AssessmentBuilderConfigurationService:
    """Construct and validate shared Mathematics 6-9 editing configurations."""

    @staticmethod
    def reference_math_thcs_3223(
        *,
        grade_level: int,
        assessment_type_code: str = "FINAL",
        semester_number: int = 1,
        duration_minutes: int = 90,
        selected_topic_codes: Sequence[str] = (),
        selected_requirement_codes: Sequence[str] = (),
    ) -> AssessmentBuilderConfiguration:
        """Return the existing repository 3-2-2-3 profile as a reference preset.

        This is an editing preset, not a claim that one structure is mandatory
        for every local assessment.
        """
        return AssessmentBuilderConfiguration(
            grade_level=grade_level,
            assessment_type_code=assessment_type_code,
            semester_number=semester_number,
            duration_minutes=duration_minutes,
            total_score=Decimal("10"),
            sections=(
                AssessmentBuilderSection(
                    section_code="MCQ",
                    question_type_code="MULTIPLE_CHOICE",
                    question_count=12,
                    response_count=12,
                    section_score=Decimal("3"),
                ),
                AssessmentBuilderSection(
                    section_code="TF",
                    question_type_code="TRUE_FALSE",
                    question_count=2,
                    response_count=8,
                    section_score=Decimal("2"),
                ),
                AssessmentBuilderSection(
                    section_code="SHORT",
                    question_type_code="SHORT_RESPONSE",
                    question_count=4,
                    response_count=4,
                    section_score=Decimal("2"),
                ),
                AssessmentBuilderSection(
                    section_code="ESSAY",
                    question_type_code="ESSAY",
                    question_count=2,
                    response_count=2,
                    section_score=Decimal("3"),
                ),
            ),
            cognitive_allocations=(
                AssessmentBuilderCognitiveAllocation(
                    "KNOW",
                    Decimal("40"),
                ),
                AssessmentBuilderCognitiveAllocation(
                    "UNDERSTAND",
                    Decimal("30"),
                ),
                AssessmentBuilderCognitiveAllocation(
                    "APPLY",
                    Decimal("30"),
                ),
            ),
            selected_topic_codes=tuple(selected_topic_codes),
            selected_requirement_codes=tuple(
                selected_requirement_codes
            ),
        )

    @staticmethod
    def validate(
        configuration: AssessmentBuilderConfiguration,
    ) -> AssessmentBuilderConfiguration:
        """Return a valid immutable configuration or raise fail-closed."""
        if not isinstance(
            configuration,
            AssessmentBuilderConfiguration,
        ):
            raise AssessmentBuilderConfigurationError(
                "configuration must be AssessmentBuilderConfiguration"
            )
        return configuration
