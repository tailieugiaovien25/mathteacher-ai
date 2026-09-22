from decimal import Decimal

import pytest

from assessment_generation_v2.services.assessment_builder_governed_defaults_service import (
    AssessmentBuilderGovernedDefaultsError,
    AssessmentBuilderGovernedDefaultsService,
    GovernedAssessmentSectionSnapshot,
    GovernedAssessmentSettingSnapshot,
    GovernedCognitiveAllocationSnapshot,
)


def setting(
    *,
    version="SETTING-1",
    grade=8,
    year="2026-2027",
    semester=1,
    assessment_type="FINAL",
    score="10",
):
    return GovernedAssessmentSettingSnapshot(
        setting_version_id=version,
        profile_code="MATH-THCS-01",
        subject_code="MATH",
        assessment_type_code=assessment_type,
        grade_level=grade,
        academic_year=year,
        semester_number=semester,
        duration_minutes=90,
        total_score=Decimal(score),
    )


def sections():
    return (
        GovernedAssessmentSectionSnapshot(
            section_code="MCQ",
            question_type_code="MCQ",
            question_count=12,
            response_count=12,
            section_score=Decimal("3"),
        ),
        GovernedAssessmentSectionSnapshot(
            section_code="TF",
            question_type_code="TRUE_FALSE",
            question_count=2,
            response_count=8,
            section_score=Decimal("2"),
        ),
        GovernedAssessmentSectionSnapshot(
            section_code="SHORT",
            question_type_code="SHORT_ANSWER",
            question_count=4,
            response_count=4,
            section_score=Decimal("2"),
        ),
        GovernedAssessmentSectionSnapshot(
            section_code="ESSAY",
            question_type_code="ESSAY",
            question_count=2,
            response_count=2,
            section_score=Decimal("3"),
        ),
    )


def allocations():
    return (
        GovernedCognitiveAllocationSnapshot(
            cognitive_level_code="NB",
            target_score=Decimal("4"),
            target_percentage=Decimal("40"),
        ),
        GovernedCognitiveAllocationSnapshot(
            cognitive_level_code="TH",
            target_score=Decimal("3"),
            target_percentage=Decimal("30"),
        ),
        GovernedCognitiveAllocationSnapshot(
            cognitive_level_code="VD",
            target_score=Decimal("3"),
            target_percentage=Decimal("30"),
        ),
    )


def test_unique_approved_setting_is_resolved_automatically():
    service = AssessmentBuilderGovernedDefaultsService()

    result = service.resolve_unique_setting(
        settings=(
            setting(
                version="S7",
                grade=7,
            ),
            setting(
                version="S8",
                grade=8,
            ),
        ),
        subject_code="math",
        assessment_type_code="FINAL",
        grade_level=8,
        academic_year="2026-2027",
        semester_number=1,
    )

    assert result.setting_version_id == "S8"


def test_no_matching_setting_fails_closed():
    service = AssessmentBuilderGovernedDefaultsService()

    with pytest.raises(
        AssessmentBuilderGovernedDefaultsError,
        match="no approved setting",
    ):
        service.resolve_unique_setting(
            settings=(setting(grade=7),),
            subject_code="MATH",
            assessment_type_code="FINAL",
            grade_level=8,
            academic_year="2026-2027",
            semester_number=1,
        )


def test_multiple_matching_settings_fail_closed():
    service = AssessmentBuilderGovernedDefaultsService()

    with pytest.raises(
        AssessmentBuilderGovernedDefaultsError,
        match="ambiguous",
    ):
        service.resolve_unique_setting(
            settings=(
                setting(version="A"),
                setting(version="B"),
            ),
            subject_code="MATH",
            assessment_type_code="FINAL",
            grade_level=8,
            academic_year="2026-2027",
            semester_number=1,
        )


def test_governed_defaults_replace_manual_structure_values():
    result = (
        AssessmentBuilderGovernedDefaultsService()
        .build(
            setting=setting(),
            sections=sections(),
            cognitive_allocations=allocations(),
        )
    )

    assert result.duration_minutes == 90
    assert result.total_score == Decimal("10")
    assert len(result.sections) == 4
    assert (
        sum(
            item.question_count
            for item in result.sections
        )
        == 20
    )
    assert (
        sum(
            item.target_percentage
            for item in result.cognitive_allocations
        )
        == Decimal("100")
    )


def test_section_scores_must_equal_total_score():
    bad_sections = list(sections())
    bad_sections[-1] = (
        GovernedAssessmentSectionSnapshot(
            section_code="ESSAY",
            question_type_code="ESSAY",
            question_count=2,
            response_count=2,
            section_score=Decimal("2"),
        )
    )

    with pytest.raises(
        AssessmentBuilderGovernedDefaultsError,
        match="section scores",
    ):
        (
            AssessmentBuilderGovernedDefaultsService()
            .build(
                setting=setting(),
                sections=tuple(bad_sections),
                cognitive_allocations=allocations(),
            )
        )


def test_cognitive_percentages_must_equal_100():
    bad = (
        GovernedCognitiveAllocationSnapshot(
            cognitive_level_code="NB",
            target_score=Decimal("4"),
            target_percentage=Decimal("40"),
        ),
        GovernedCognitiveAllocationSnapshot(
            cognitive_level_code="TH",
            target_score=Decimal("3"),
            target_percentage=Decimal("30"),
        ),
        GovernedCognitiveAllocationSnapshot(
            cognitive_level_code="VD",
            target_score=Decimal("3"),
            target_percentage=Decimal("20"),
        ),
    )

    with pytest.raises(
        AssessmentBuilderGovernedDefaultsError,
        match="percentages",
    ):
        (
            AssessmentBuilderGovernedDefaultsService()
            .build(
                setting=setting(),
                sections=sections(),
                cognitive_allocations=bad,
            )
        )


def test_duplicate_section_codes_fail_closed():
    duplicate = sections() + (
        GovernedAssessmentSectionSnapshot(
            section_code="MCQ",
            question_type_code="MCQ",
            question_count=1,
            response_count=1,
            section_score=Decimal("1"),
        ),
    )

    with pytest.raises(
        AssessmentBuilderGovernedDefaultsError,
        match="duplicate section_code",
    ):
        (
            AssessmentBuilderGovernedDefaultsService()
            .build(
                setting=setting(score="11"),
                sections=duplicate,
                cognitive_allocations=(
                    GovernedCognitiveAllocationSnapshot(
                        cognitive_level_code="NB",
                        target_score=Decimal("11"),
                        target_percentage=Decimal("100"),
                    ),
                ),
            )
        )


def test_assessment_type_is_part_of_unique_setting_identity():
    service = AssessmentBuilderGovernedDefaultsService()

    result = service.resolve_unique_setting(
        settings=(
            setting(version="MID", assessment_type="MIDTERM"),
            setting(version="FIN", assessment_type="FINAL"),
        ),
        subject_code="MATH",
        assessment_type_code="MIDTERM",
        grade_level=8,
        academic_year="2026-2027",
        semester_number=1,
    )

    assert result.setting_version_id == "MID"
