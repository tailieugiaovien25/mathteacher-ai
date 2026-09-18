from decimal import Decimal

import pytest

from assessment_generation_v2.services.assessment_builder_configuration_service import (
    AssessmentBuilderConfiguration,
    AssessmentBuilderConfigurationError,
    AssessmentBuilderConfigurationService,
)


@pytest.mark.parametrize("grade_level", [6, 7, 8, 9])
def test_reference_configuration_supports_math_thcs_grades(
    grade_level: int,
) -> None:
    config = AssessmentBuilderConfigurationService.reference_math_thcs_3223(
        grade_level=grade_level,
    )
    assert config.subject_code == "MATH"
    assert config.grade_level == grade_level
    assert config.total_score == Decimal("10")
    assert [row.question_type_code for row in config.sections] == [
        "MULTIPLE_CHOICE",
        "TRUE_FALSE",
        "SHORT_RESPONSE",
        "ESSAY",
    ]
    assert sum(
        (row.section_score for row in config.sections),
        Decimal("0"),
    ) == Decimal("10")
    assert sum(
        (row.target_percentage for row in config.cognitive_allocations),
        Decimal("0"),
    ) == Decimal("100")


@pytest.mark.parametrize("assessment_type", ["REGULAR", "MIDTERM", "FINAL"])
def test_reference_configuration_supports_all_requested_types(
    assessment_type: str,
) -> None:
    config = AssessmentBuilderConfigurationService.reference_math_thcs_3223(
        grade_level=8,
        assessment_type_code=assessment_type,
    )
    assert config.assessment_type_code == assessment_type


def test_configuration_normalizes_unique_scope_codes() -> None:
    config = AssessmentBuilderConfigurationService.reference_math_thcs_3223(
        grade_level=9,
        selected_topic_codes=(" T1 ", "T1", "", "T2"),
        selected_requirement_codes=("R1", " R1 ", "R2"),
    )
    assert config.selected_topic_codes == ("T1", "T2")
    assert config.selected_requirement_codes == ("R1", "R2")


def test_configuration_fails_closed_outside_grade_6_9() -> None:
    with pytest.raises(
        AssessmentBuilderConfigurationError,
        match="grade_level",
    ):
        AssessmentBuilderConfigurationService.reference_math_thcs_3223(
            grade_level=10,
        )


def test_configuration_fails_closed_when_scores_do_not_sum() -> None:
    valid = AssessmentBuilderConfigurationService.reference_math_thcs_3223(
        grade_level=6,
    )
    with pytest.raises(
        AssessmentBuilderConfigurationError,
        match="section scores",
    ):
        AssessmentBuilderConfiguration(
            grade_level=valid.grade_level,
            assessment_type_code=valid.assessment_type_code,
            semester_number=valid.semester_number,
            duration_minutes=valid.duration_minutes,
            total_score=Decimal("9"),
            sections=valid.sections,
            cognitive_allocations=valid.cognitive_allocations,
        )
