"""Read-only structural matrix preview for Mathematics 6-9 assessments."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from assessment_generation_v2.services.assessment_builder_configuration_service import (
    COGNITIVE_LEVEL_LABELS,
    QUESTION_TYPE_LABELS,
    AssessmentBuilderConfiguration,
    AssessmentBuilderConfigurationService,
)


@dataclass(frozen=True, slots=True)
class AssessmentBuilderSectionPreviewRow:
    section_code: str
    question_type_code: str
    question_type_name: str
    question_count: int
    response_count: int
    section_score: Decimal
    score_percentage: Decimal


@dataclass(frozen=True, slots=True)
class AssessmentBuilderCognitivePreviewRow:
    cognitive_level_code: str
    cognitive_level_name: str
    target_percentage: Decimal
    target_score: Decimal


@dataclass(frozen=True, slots=True)
class AssessmentBuilderMatrixPreview:
    grade_level: int
    assessment_type_code: str
    semester_number: int
    duration_minutes: int
    total_score: Decimal
    section_rows: tuple[AssessmentBuilderSectionPreviewRow, ...]
    cognitive_rows: tuple[AssessmentBuilderCognitivePreviewRow, ...]
    selected_topic_codes: tuple[str, ...]
    selected_requirement_codes: tuple[str, ...]
    is_structural_preview: bool = True


class AssessmentBuilderMatrixPreviewService:
    """Build deterministic previews without database or publication effects."""

    def __init__(self) -> None:
        self._configuration_service = AssessmentBuilderConfigurationService()

    def build(
        self,
        configuration: AssessmentBuilderConfiguration,
    ) -> AssessmentBuilderMatrixPreview:
        configuration = self._configuration_service.validate(configuration)
        total_score = configuration.total_score

        section_rows = tuple(
            AssessmentBuilderSectionPreviewRow(
                section_code=section.section_code,
                question_type_code=section.question_type_code,
                question_type_name=QUESTION_TYPE_LABELS[
                    section.question_type_code
                ],
                question_count=section.question_count,
                response_count=section.response_count,
                section_score=section.section_score,
                score_percentage=(
                    section.section_score * Decimal("100") / total_score
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            )
            for section in configuration.sections
        )

        cognitive_rows = tuple(
            AssessmentBuilderCognitivePreviewRow(
                cognitive_level_code=allocation.cognitive_level_code,
                cognitive_level_name=COGNITIVE_LEVEL_LABELS[
                    allocation.cognitive_level_code
                ],
                target_percentage=allocation.target_percentage,
                target_score=(
                    total_score
                    * allocation.target_percentage
                    / Decimal("100")
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            )
            for allocation in configuration.cognitive_allocations
        )

        return AssessmentBuilderMatrixPreview(
            grade_level=configuration.grade_level,
            assessment_type_code=configuration.assessment_type_code,
            semester_number=configuration.semester_number,
            duration_minutes=configuration.duration_minutes,
            total_score=configuration.total_score,
            section_rows=section_rows,
            cognitive_rows=cognitive_rows,
            selected_topic_codes=configuration.selected_topic_codes,
            selected_requirement_codes=configuration.selected_requirement_codes,
        )
