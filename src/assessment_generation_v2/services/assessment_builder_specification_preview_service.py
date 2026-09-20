"""Preliminary non-canonical specification preview for the Math 6-9 builder.

This module is deliberately editing-only. It derives a human-readable preview
from the already validated builder configuration and structural matrix preview.
It does not persist data, resolve canonical curriculum, infer topic-to-cell
mappings, or read candidate mapping artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from assessment_generation_v2.services.assessment_builder_configuration_service import (
    AssessmentBuilderConfiguration,
    AssessmentBuilderConfigurationService,
)
from assessment_generation_v2.services.assessment_builder_matrix_preview_service import (
    AssessmentBuilderCognitivePreviewRow,
    AssessmentBuilderMatrixPreview,
    AssessmentBuilderMatrixPreviewService,
    AssessmentBuilderSectionPreviewRow,
)


PRELIMINARY_NON_CANONICAL = "PRELIMINARY_NON_CANONICAL"


class AssessmentBuilderSpecificationPreviewError(ValueError):
    """Raised when a preliminary specification preview cannot be derived safely."""


@dataclass(frozen=True, slots=True)
class AssessmentBuilderSpecificationPreview:
    authority_code: str
    authority_label: str
    authority_note: str
    grade_level: int
    assessment_type_code: str
    semester_number: int
    duration_minutes: int
    total_score: Decimal
    section_rows: tuple[AssessmentBuilderSectionPreviewRow, ...]
    cognitive_rows: tuple[AssessmentBuilderCognitivePreviewRow, ...]
    selected_topic_codes: tuple[str, ...]
    selected_requirement_codes: tuple[str, ...]
    is_canonical: bool = False
    is_preliminary: bool = True

    def __post_init__(self) -> None:
        if self.authority_code != PRELIMINARY_NON_CANONICAL:
            raise AssessmentBuilderSpecificationPreviewError(
                "authority_code must be PRELIMINARY_NON_CANONICAL"
            )
        if self.is_canonical:
            raise AssessmentBuilderSpecificationPreviewError(
                "preliminary specification preview must not be canonical"
            )
        if not self.is_preliminary:
            raise AssessmentBuilderSpecificationPreviewError(
                "preliminary specification preview must remain preliminary"
            )


class AssessmentBuilderSpecificationPreviewService:
    """Build a deterministic editing preview without persistence or authority."""

    def __init__(self) -> None:
        self._configuration_service = AssessmentBuilderConfigurationService()
        self._matrix_preview_service = AssessmentBuilderMatrixPreviewService()

    def build(
        self,
        *,
        configuration: AssessmentBuilderConfiguration,
        matrix_preview: AssessmentBuilderMatrixPreview,
    ) -> AssessmentBuilderSpecificationPreview:
        configuration = self._configuration_service.validate(configuration)

        if not isinstance(matrix_preview, AssessmentBuilderMatrixPreview):
            raise AssessmentBuilderSpecificationPreviewError(
                "matrix_preview must be AssessmentBuilderMatrixPreview"
            )

        expected_preview = self._matrix_preview_service.build(configuration)
        if matrix_preview != expected_preview:
            raise AssessmentBuilderSpecificationPreviewError(
                "matrix_preview does not match the validated builder configuration"
            )

        return AssessmentBuilderSpecificationPreview(
            authority_code=PRELIMINARY_NON_CANONICAL,
            authority_label=(
                "BẢN ĐẶC TẢ SƠ BỘ — PRELIMINARY / NON-CANONICAL"
            ),
            authority_note=(
                "Bản xem trước này chỉ phản ánh cấu trúc đề và các mã phạm vi "
                "do giáo viên đang chọn. Hệ thống chưa xác nhận canonical và "
                "không tự suy đoán nội dung/YCCĐ hay gán chúng vào ô ma trận."
            ),
            grade_level=matrix_preview.grade_level,
            assessment_type_code=matrix_preview.assessment_type_code,
            semester_number=matrix_preview.semester_number,
            duration_minutes=matrix_preview.duration_minutes,
            total_score=matrix_preview.total_score,
            section_rows=matrix_preview.section_rows,
            cognitive_rows=matrix_preview.cognitive_rows,
            selected_topic_codes=matrix_preview.selected_topic_codes,
            selected_requirement_codes=matrix_preview.selected_requirement_codes,
        )
