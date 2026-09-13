from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from assessment_generation_v2.services.assessment_curriculum_query_service import (
    AssessmentLearningRequirement,
)
from assessment_generation_v2.services.assessment_foundation import (
    AssessmentConfig,
    AssessmentFoundationError,
    AssessmentScope,
    AssessmentSpecification,
    AssessmentStructure,
    CognitiveAllocation,
    CompetencyRequirement,
    MathAssessmentPolicyError,
    MatrixCell,
    QuestionRequirement,
    ValidationResult,
    ValidationSemanticsLossError,
    ValidationStatus,
    validate_math_application_grade,
    validate_math_assessment_config,
    validation_result_from_legacy,
    validation_result_to_legacy,
)
from assessment_generation_v2.services.assessment_matrix_cell_authoring import (
    AssessmentMatrixCell,
    AssessmentProfileSectionOption,
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


def _config(grade_level: int = 6) -> AssessmentConfig:
    return AssessmentConfig(
        config_code=f"MATH-{grade_level}-MIDTERM",
        title=f"Math {grade_level} midterm",
        subject_code="math",
        grade_level=grade_level,
        academic_year="2026-2027",
        semester="hk1",
        test_type="midterm",
        duration_minutes=90,
        total_score="10.0",
        variant_count=2,
    )


def _requirement(code: str, *, topic_code: str = "TOPIC-1") -> CompetencyRequirement:
    return CompetencyRequirement(
        requirement_code=code,
        program_code="CT2018-MATH",
        topic_code=topic_code,
        grade_level=6,
        requirement_text=f"Canonical curriculum evidence for {code}",
        source_locator="CTGDPT 2018, page 42",
        version_number=3,
        status="ACTIVE",
        canonical_status="VERIFIED",
    )


def _specification() -> AssessmentSpecification:
    sections = (
        AssessmentProfileSectionOption(
            "ESSAY", "Essay", "ESSAY", 20, 1, 1, "6"
        ),
        AssessmentProfileSectionOption(
            "MCQ", "Multiple choice", "MULTIPLE_CHOICE", 10, 2, 2, "4"
        ),
    )
    requirements = (_requirement("REQ-2"), _requirement("REQ-1"))
    return AssessmentSpecification(
        specification_code="math-6-spec",
        title="Canonical Math 6 specification",
        config=_config(),
        scope=AssessmentScope(
            subject_code="MATH",
            grade_level=6,
            program_code="CT2018-MATH",
            selected_topic_codes=("TOPIC-1",),
            selected_requirement_codes=("REQ-1", "REQ-2"),
            selected_requirements=requirements,
            finalized=True,
        ),
        structure=AssessmentStructure(sections),
        cognitive_allocations=(
            CognitiveAllocation("APPLY", "6", "60"),
            CognitiveAllocation("KNOW", "4", "40"),
        ),
        competency_requirements=requirements,
        requirement_assignments=(
            BlueprintRequirementAssignment("REQ-2", "SUPPORTING", 1, 20, "6"),
            BlueprintRequirementAssignment("REQ-1", "PRIMARY", 2, 10, "4"),
        ),
        matrix_cells=(
            MatrixCell("ESSAY", "TOPIC-1", "APPLY", 1, 1, "6", 20),
            MatrixCell("MCQ", "TOPIC-1", "KNOW", 2, 2, "4", 10),
        ),
        question_requirements=(
            QuestionRequirement("QR-ESSAY", 20, ("REQ-2",), 1, 1, "6"),
            QuestionRequirement("QR-MCQ", 10, ("REQ-1",), 2, 2, "4"),
        ),
    )


@pytest.mark.parametrize("grade_level", (1, 12))
def test_domain_accepts_boundary_grades(grade_level: int) -> None:
    assert _config(grade_level).grade_level == grade_level


@pytest.mark.parametrize("grade_level", (True, False))
def test_domain_rejects_boolean_grades(grade_level: bool) -> None:
    with pytest.raises(TypeError, match="integer"):
        _config(grade_level)


@pytest.mark.parametrize("grade_level", (0, 13))
def test_domain_rejects_grades_outside_one_through_twelve(
    grade_level: int,
) -> None:
    with pytest.raises(AssessmentFoundationError, match="1 and 12"):
        _config(grade_level)


@pytest.mark.parametrize("grade_level", (1, 5, 10, 12))
def test_math_policy_separately_rejects_grades_outside_six_through_nine(
    grade_level: int,
) -> None:
    config = _config(grade_level)
    with pytest.raises(MathAssessmentPolicyError, match="6 through 9"):
        validate_math_assessment_config(config)


@pytest.mark.parametrize("grade_level", (6, 7, 8, 9))
def test_math_policy_accepts_grades_six_through_nine(
    grade_level: int,
) -> None:
    config = _config(grade_level)
    assert validate_math_application_grade(grade_level) == grade_level
    assert validate_math_assessment_config(config) is config


def test_grades_seven_eight_nine_use_the_same_canonical_classes() -> None:
    configs = tuple(_config(grade) for grade in (7, 8, 9))
    assert all(type(config) is AssessmentConfig for config in configs)
    assert len({type(config) for config in configs}) == 1


def test_canonical_aliases_reuse_existing_types_and_preserve_evidence() -> None:
    requirement = _requirement("REQ-1")
    assert CompetencyRequirement is AssessmentLearningRequirement
    assert CognitiveAllocation is ProfileLevelAllocation
    assert MatrixCell is AssessmentMatrixCell
    assert AssessmentScope is CanonicalAssessmentSelection
    assert requirement.requirement_text == "Canonical curriculum evidence for REQ-1"
    assert requirement.source_locator == "CTGDPT 2018, page 42"
    assert requirement.version_number == 3
    assert requirement.status == "ACTIVE"
    assert requirement.canonical_status == "VERIFIED"


def test_assignment_is_distinct_from_competency_evidence() -> None:
    assignment = BlueprintRequirementAssignment("REQ-1", "PRIMARY", 2, 10, "4")
    evidence = _requirement("REQ-1")
    assert type(assignment) is not type(evidence)
    assert not isinstance(assignment, AssessmentLearningRequirement)
    assert assignment.requirement_code == evidence.requirement_code


def test_structure_totals_and_order_are_deterministic() -> None:
    specification = _specification()
    structure = specification.structure
    assert tuple(row.section_code for row in structure.sections) == ("MCQ", "ESSAY")
    assert structure.question_count == 3
    assert structure.response_count == 3
    assert structure.total_score == Decimal("10")
    assert tuple(row.sequence_number for row in specification.matrix_cells) == (10, 20)

    duplicate_sequence = (
        AssessmentProfileSectionOption("A", "A", "ESSAY", 10, 1, 1, "5"),
        AssessmentProfileSectionOption("B", "B", "ESSAY", 10, 1, 1, "5"),
    )
    with pytest.raises(AssessmentFoundationError, match="sequences"):
        AssessmentStructure(duplicate_sequence)


def test_question_requirements_reference_canonical_codes_and_partition_cells() -> None:
    specification = _specification()
    assert specification.question_requirements[0].competency_requirement_codes == (
        "REQ-1",
    )

    unknown = replace(
        specification.question_requirements[0],
        competency_requirement_codes=("REQ-UNKNOWN",),
    )
    with pytest.raises(AssessmentFoundationError, match="unknown canonical"):
        replace(
            specification,
            question_requirements=(unknown, specification.question_requirements[1]),
        )

    wrong_total = replace(specification.question_requirements[0], target_score="3")
    with pytest.raises(AssessmentFoundationError, match="exactly partition"):
        replace(
            specification,
            question_requirements=(wrong_total, specification.question_requirements[1]),
        )


def test_matrix_and_specification_cross_contract_validation() -> None:
    specification = _specification()
    bad_cell = replace(specification.matrix_cells[0], section_code="UNKNOWN")
    with pytest.raises(AssessmentFoundationError, match="unknown section"):
        replace(
            specification,
            matrix_cells=(bad_cell, specification.matrix_cells[1]),
        )

    wrong_assignment = replace(
        specification.requirement_assignments[0], requirement_code="REQ-UNKNOWN"
    )
    with pytest.raises(AssessmentFoundationError, match="must match"):
        replace(
            specification,
            requirement_assignments=(
                wrong_assignment,
                specification.requirement_assignments[1],
            ),
        )


def test_pass_warning_fail_semantics_are_distinct() -> None:
    passed = ValidationResult(ValidationStatus.PASS)
    warning = ValidationResult(ValidationStatus.WARNING, warnings=("Confirm scope",))
    failed = ValidationResult(ValidationStatus.FAIL, errors=("Score mismatch",))
    assert passed.may_continue_automatically and not passed.blocked
    assert warning.requires_teacher_confirmation
    assert not warning.may_continue_automatically and not warning.blocked
    assert failed.blocked and not failed.may_continue_automatically


def test_legacy_reports_convert_to_canonical_pass_and_fail() -> None:
    passed = validation_result_from_legacy(AssessmentValidationReport(True))
    failed = validation_result_from_legacy(
        AssessmentValidationReport(False, ("Legacy violation",))
    )
    assert passed.status is ValidationStatus.PASS
    assert failed.status is ValidationStatus.FAIL
    assert failed.errors == ("Legacy violation",)


def test_canonical_pass_and_fail_convert_to_legacy_reports() -> None:
    passed = validation_result_to_legacy(ValidationResult(ValidationStatus.PASS))
    failed = validation_result_to_legacy(
        ValidationResult(ValidationStatus.FAIL, errors=("Canonical error",))
    )
    assert passed.is_valid is True
    assert failed.is_valid is False
    assert failed.violations == ("Canonical error",)


def test_canonical_warning_cannot_be_lossily_converted() -> None:
    warning = ValidationResult(
        ValidationStatus.WARNING,
        warnings=("Teacher confirmation is required",),
    )
    with pytest.raises(ValidationSemanticsLossError, match="cannot be represented"):
        validation_result_to_legacy(warning)
