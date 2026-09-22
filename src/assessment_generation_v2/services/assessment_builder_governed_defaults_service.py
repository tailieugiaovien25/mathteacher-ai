"""Governed defaults for the Mathematics 6-9 assessment builder.

This service is pure and persistence-free. It receives approved-setting/profile
snapshots already loaded by the authenticated runtime and turns them into a
validated builder-default snapshot.

Teacher choices remain teacher choices (grade, assessment type, semester).
Governed structural values such as duration, score, question-section structure,
and cognitive allocation are not re-entered when an unambiguous approved
setting/profile is available.

Approved setting snapshots carry assessment_type_code explicitly. Automatic
setting selection is fail-closed unless exactly one approved setting matches
subject + grade + assessment type + academic year + semester.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Sequence


class AssessmentBuilderGovernedDefaultsError(ValueError):
    """Raised when governed builder defaults are missing or ambiguous."""


def _text(value: object, field: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise AssessmentBuilderGovernedDefaultsError(
            f"{field} must not be empty"
        )
    return normalized


def _decimal(value: object, field: str) -> Decimal:
    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise AssessmentBuilderGovernedDefaultsError(
            f"{field} must be a valid number"
        ) from error

    if not normalized.is_finite():
        raise AssessmentBuilderGovernedDefaultsError(
            f"{field} must be finite"
        )

    return normalized


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool):
        raise AssessmentBuilderGovernedDefaultsError(
            f"{field} must be positive"
        )

    try:
        normalized = int(value)
    except (TypeError, ValueError) as error:
        raise AssessmentBuilderGovernedDefaultsError(
            f"{field} must be positive"
        ) from error

    if normalized < 1:
        raise AssessmentBuilderGovernedDefaultsError(
            f"{field} must be positive"
        )

    return normalized


@dataclass(frozen=True, slots=True)
class GovernedAssessmentSettingSnapshot:
    setting_version_id: str
    profile_code: str
    subject_code: str
    assessment_type_code: str
    grade_level: int
    academic_year: str
    semester_number: int | None
    duration_minutes: int
    total_score: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "setting_version_id",
            _text(
                self.setting_version_id,
                "setting_version_id",
            ),
        )
        object.__setattr__(
            self,
            "profile_code",
            _text(
                self.profile_code,
                "profile_code",
            ).upper(),
        )
        object.__setattr__(
            self,
            "subject_code",
            _text(
                self.subject_code,
                "subject_code",
            ).upper(),
        )

        assessment_type = _text(
            self.assessment_type_code,
            "assessment_type_code",
        ).upper()
        if assessment_type not in {"REGULAR", "MIDTERM", "FINAL"}:
            raise AssessmentBuilderGovernedDefaultsError(
                "assessment_type_code must be REGULAR, MIDTERM, or FINAL"
            )
        object.__setattr__(
            self,
            "assessment_type_code",
            assessment_type,
        )

        grade = _positive_int(
            self.grade_level,
            "grade_level",
        )
        if grade not in {6, 7, 8, 9}:
            raise AssessmentBuilderGovernedDefaultsError(
                "grade_level must be one of 6, 7, 8, 9"
            )
        object.__setattr__(
            self,
            "grade_level",
            grade,
        )

        object.__setattr__(
            self,
            "academic_year",
            _text(
                self.academic_year,
                "academic_year",
            ),
        )

        if self.semester_number is not None:
            semester = _positive_int(
                self.semester_number,
                "semester_number",
            )
            if semester not in {1, 2}:
                raise AssessmentBuilderGovernedDefaultsError(
                    "semester_number must be 1, 2, or None"
                )
            object.__setattr__(
                self,
                "semester_number",
                semester,
            )

        object.__setattr__(
            self,
            "duration_minutes",
            _positive_int(
                self.duration_minutes,
                "duration_minutes",
            ),
        )

        score = _decimal(
            self.total_score,
            "total_score",
        )
        if score <= 0:
            raise AssessmentBuilderGovernedDefaultsError(
                "total_score must be positive"
            )
        object.__setattr__(
            self,
            "total_score",
            score,
        )


@dataclass(frozen=True, slots=True)
class GovernedAssessmentSectionSnapshot:
    section_code: str
    question_type_code: str
    question_count: int
    response_count: int
    section_score: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "section_code",
            _text(
                self.section_code,
                "section_code",
            ).upper(),
        )
        object.__setattr__(
            self,
            "question_type_code",
            _text(
                self.question_type_code,
                "question_type_code",
            ).upper(),
        )

        question_count = _positive_int(
            self.question_count,
            "question_count",
        )
        response_count = _positive_int(
            self.response_count,
            "response_count",
        )

        if response_count < question_count:
            raise AssessmentBuilderGovernedDefaultsError(
                "response_count must be >= question_count"
            )

        object.__setattr__(
            self,
            "question_count",
            question_count,
        )
        object.__setattr__(
            self,
            "response_count",
            response_count,
        )

        score = _decimal(
            self.section_score,
            "section_score",
        )
        if score <= 0:
            raise AssessmentBuilderGovernedDefaultsError(
                "section_score must be positive"
            )
        object.__setattr__(
            self,
            "section_score",
            score,
        )


@dataclass(frozen=True, slots=True)
class GovernedCognitiveAllocationSnapshot:
    cognitive_level_code: str
    target_score: Decimal
    target_percentage: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "cognitive_level_code",
            _text(
                self.cognitive_level_code,
                "cognitive_level_code",
            ).upper(),
        )

        score = _decimal(
            self.target_score,
            "target_score",
        )
        percentage = _decimal(
            self.target_percentage,
            "target_percentage",
        )

        if score <= 0:
            raise AssessmentBuilderGovernedDefaultsError(
                "target_score must be positive"
            )
        if percentage <= 0:
            raise AssessmentBuilderGovernedDefaultsError(
                "target_percentage must be positive"
            )

        object.__setattr__(
            self,
            "target_score",
            score,
        )
        object.__setattr__(
            self,
            "target_percentage",
            percentage,
        )


@dataclass(frozen=True, slots=True)
class AssessmentBuilderGovernedDefaults:
    setting: GovernedAssessmentSettingSnapshot
    sections: tuple[
        GovernedAssessmentSectionSnapshot,
        ...,
    ]
    cognitive_allocations: tuple[
        GovernedCognitiveAllocationSnapshot,
        ...,
    ]

    @property
    def duration_minutes(self) -> int:
        return self.setting.duration_minutes

    @property
    def total_score(self) -> Decimal:
        return self.setting.total_score


class AssessmentBuilderGovernedDefaultsService:
    """Resolve and validate system-governed builder defaults."""

    def resolve_unique_setting(
        self,
        *,
        settings: Sequence[
            GovernedAssessmentSettingSnapshot
        ],
        subject_code: str,
        assessment_type_code: str,
        grade_level: int,
        academic_year: str,
        semester_number: int,
    ) -> GovernedAssessmentSettingSnapshot:
        subject = _text(
            subject_code,
            "subject_code",
        ).upper()
        assessment_type = _text(
            assessment_type_code,
            "assessment_type_code",
        ).upper()
        if assessment_type not in {"REGULAR", "MIDTERM", "FINAL"}:
            raise AssessmentBuilderGovernedDefaultsError(
                "assessment_type_code must be REGULAR, MIDTERM, or FINAL"
            )

        year = _text(
            academic_year,
            "academic_year",
        )
        grade = _positive_int(
            grade_level,
            "grade_level",
        )
        semester = _positive_int(
            semester_number,
            "semester_number",
        )

        if grade not in {6, 7, 8, 9}:
            raise AssessmentBuilderGovernedDefaultsError(
                "grade_level must be one of 6, 7, 8, 9"
            )
        if semester not in {1, 2}:
            raise AssessmentBuilderGovernedDefaultsError(
                "semester_number must be 1 or 2"
            )

        matches = tuple(
            item
            for item in settings
            if (
                item.subject_code == subject
                and item.assessment_type_code == assessment_type
                and item.grade_level == grade
                and item.academic_year == year
                and item.semester_number == semester
            )
        )

        if not matches:
            raise AssessmentBuilderGovernedDefaultsError(
                "no approved setting matches the current "
                "subject/grade/assessment-type/academic-year/semester selection"
            )

        if len(matches) != 1:
            raise AssessmentBuilderGovernedDefaultsError(
                "approved setting is ambiguous; exactly one "
                "matching setting is required for automatic defaults"
            )

        return matches[0]

    def build(
        self,
        *,
        setting: GovernedAssessmentSettingSnapshot,
        sections: Sequence[
            GovernedAssessmentSectionSnapshot
        ],
        cognitive_allocations: Sequence[
            GovernedCognitiveAllocationSnapshot
        ],
    ) -> AssessmentBuilderGovernedDefaults:
        normalized_sections = tuple(sections)
        normalized_allocations = tuple(
            cognitive_allocations
        )

        if not normalized_sections:
            raise AssessmentBuilderGovernedDefaultsError(
                "profile sections must not be empty"
            )
        if not normalized_allocations:
            raise AssessmentBuilderGovernedDefaultsError(
                "cognitive allocations must not be empty"
            )

        section_codes = tuple(
            item.section_code
            for item in normalized_sections
        )
        if len(set(section_codes)) != len(section_codes):
            raise AssessmentBuilderGovernedDefaultsError(
                "duplicate section_code is not allowed"
            )

        cognitive_codes = tuple(
            item.cognitive_level_code
            for item in normalized_allocations
        )
        if (
            len(set(cognitive_codes))
            != len(cognitive_codes)
        ):
            raise AssessmentBuilderGovernedDefaultsError(
                "duplicate cognitive_level_code is not allowed"
            )

        section_score_total = sum(
            (
                item.section_score
                for item in normalized_sections
            ),
            Decimal("0"),
        )

        if section_score_total != setting.total_score:
            raise AssessmentBuilderGovernedDefaultsError(
                "profile section scores must equal setting total_score"
            )

        cognitive_score_total = sum(
            (
                item.target_score
                for item in normalized_allocations
            ),
            Decimal("0"),
        )

        if cognitive_score_total != setting.total_score:
            raise AssessmentBuilderGovernedDefaultsError(
                "cognitive target scores must equal setting total_score"
            )

        cognitive_percentage_total = sum(
            (
                item.target_percentage
                for item in normalized_allocations
            ),
            Decimal("0"),
        )

        if cognitive_percentage_total != Decimal("100"):
            raise AssessmentBuilderGovernedDefaultsError(
                "cognitive target percentages must equal 100"
            )

        return AssessmentBuilderGovernedDefaults(
            setting=setting,
            sections=normalized_sections,
            cognitive_allocations=normalized_allocations,
        )
