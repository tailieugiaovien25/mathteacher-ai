from decimal import Decimal

from assessment_generation_v2.services.assessment_builder_configuration_service import (
    AssessmentBuilderConfigurationService,
)
from assessment_generation_v2.services.assessment_builder_matrix_preview_service import (
    AssessmentBuilderMatrixPreviewService,
)


def test_matrix_preview_preserves_reference_structure() -> None:
    config = AssessmentBuilderConfigurationService.reference_math_thcs_3223(
        grade_level=7,
        assessment_type_code="MIDTERM",
        semester_number=2,
        selected_topic_codes=("M7.A", "M7.B"),
        selected_requirement_codes=("M7.R1",),
    )
    preview = AssessmentBuilderMatrixPreviewService().build(config)

    assert preview.is_structural_preview is True
    assert preview.grade_level == 7
    assert preview.assessment_type_code == "MIDTERM"
    assert preview.semester_number == 2
    assert preview.total_score == Decimal("10")
    assert [row.section_score for row in preview.section_rows] == [
        Decimal("3"),
        Decimal("2"),
        Decimal("2"),
        Decimal("3"),
    ]
    assert [row.score_percentage for row in preview.section_rows] == [
        Decimal("30.00"),
        Decimal("20.00"),
        Decimal("20.00"),
        Decimal("30.00"),
    ]
    assert [row.target_score for row in preview.cognitive_rows] == [
        Decimal("4.00"),
        Decimal("3.00"),
        Decimal("3.00"),
    ]
    assert preview.selected_topic_codes == ("M7.A", "M7.B")
    assert preview.selected_requirement_codes == ("M7.R1",)


def test_matrix_preview_has_no_persistence_contract() -> None:
    service = AssessmentBuilderMatrixPreviewService()
    assert not hasattr(service, "save")
    assert not hasattr(service, "publish")
    assert not hasattr(service, "submit")
