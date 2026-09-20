from decimal import Decimal
from pathlib import Path

import pytest

from assessment_generation_v2.services.assessment_builder_configuration_service import (
    AssessmentBuilderConfigurationService,
)
from assessment_generation_v2.services.assessment_builder_matrix_preview_service import (
    AssessmentBuilderMatrixPreviewService,
)
from assessment_generation_v2.services.assessment_builder_specification_preview_service import (
    PRELIMINARY_NON_CANONICAL,
    AssessmentBuilderSpecificationPreviewError,
    AssessmentBuilderSpecificationPreviewService,
)


SERVICE_FILE = Path(
    "src/assessment_generation_v2/services/"
    "assessment_builder_specification_preview_service.py"
)
UI_FILE = Path("src/portal_v2/ui/assessment_builder_streamlit.py")


def _configuration(*, grade_level: int = 7):
    return AssessmentBuilderConfigurationService.reference_math_thcs_3223(
        grade_level=grade_level,
        assessment_type_code="MIDTERM",
        semester_number=2,
        selected_topic_codes=("MANUAL-TOPIC-A", "MANUAL-TOPIC-B"),
        selected_requirement_codes=("MANUAL-REQ-1", "MANUAL-REQ-2"),
    )


def test_preview_is_explicitly_preliminary_non_canonical() -> None:
    configuration = _configuration()
    matrix_preview = AssessmentBuilderMatrixPreviewService().build(configuration)

    result = AssessmentBuilderSpecificationPreviewService().build(
        configuration=configuration,
        matrix_preview=matrix_preview,
    )

    assert result.authority_code == PRELIMINARY_NON_CANONICAL
    assert result.is_canonical is False
    assert result.is_preliminary is True
    assert "PRELIMINARY / NON-CANONICAL" in result.authority_label
    assert "chưa xác nhận canonical" in result.authority_note


def test_preview_preserves_structure_cognition_and_manual_scope_codes() -> None:
    configuration = _configuration()
    matrix_preview = AssessmentBuilderMatrixPreviewService().build(configuration)

    result = AssessmentBuilderSpecificationPreviewService().build(
        configuration=configuration,
        matrix_preview=matrix_preview,
    )

    assert result.grade_level == 7
    assert result.assessment_type_code == "MIDTERM"
    assert result.semester_number == 2
    assert result.duration_minutes == 90
    assert result.total_score == Decimal("10")
    assert [row.section_score for row in result.section_rows] == [
        Decimal("3"),
        Decimal("2"),
        Decimal("2"),
        Decimal("3"),
    ]
    assert [row.target_score for row in result.cognitive_rows] == [
        Decimal("4.00"),
        Decimal("3.00"),
        Decimal("3.00"),
    ]
    assert result.selected_topic_codes == (
        "MANUAL-TOPIC-A",
        "MANUAL-TOPIC-B",
    )
    assert result.selected_requirement_codes == (
        "MANUAL-REQ-1",
        "MANUAL-REQ-2",
    )


def test_preview_rejects_matrix_from_another_configuration() -> None:
    configuration = _configuration(grade_level=7)
    other_configuration = _configuration(grade_level=8)
    wrong_preview = AssessmentBuilderMatrixPreviewService().build(
        other_configuration
    )

    with pytest.raises(
        AssessmentBuilderSpecificationPreviewError,
        match="does not match",
    ):
        AssessmentBuilderSpecificationPreviewService().build(
            configuration=configuration,
            matrix_preview=wrong_preview,
        )


def test_preview_service_has_no_persistence_or_canonical_domain_dependency() -> None:
    service = AssessmentBuilderSpecificationPreviewService()
    assert not hasattr(service, "save")
    assert not hasattr(service, "publish")
    assert not hasattr(service, "submit")

    text = SERVICE_FILE.read_text(encoding="utf-8-sig").lower()
    forbidden = (
        "assessmentfoundation",
        "assessmentspecification",
        "blueprintrequirementlinkservice",
        "build_default_matrix_cell_rows",
        "from supabase",
        "import supabase",
        "streamlit",
        "json.load",
        "candidate_dataset",
        "textbook_requirement_mappings.json",
    )
    for signal in forbidden:
        assert signal not in text


def test_builder_ui_uses_preview_service_without_autofill_or_persistence() -> None:
    text = UI_FILE.read_text(encoding="utf-8-sig")

    assert (
        "assessment_builder_specification_preview_service"
        in text
    )
    assert "AssessmentBuilderSpecificationPreviewService().build(" in text
    assert "specification_preview.authority_label" in text
    assert "specification_preview.authority_note" in text
    assert "Mã chủ đề do giáo viên chọn" in text
    assert "Mã YCCĐ do giáo viên chọn" in text

    assert (
        "A2-MATH69 sẽ nối chủ đề, nội dung và yêu cầu cần đạt canonical"
        not in text
    )
    assert "topic_text = specification_preview" not in text
    assert "requirement_text = specification_preview" not in text
    assert ".save(" not in text
