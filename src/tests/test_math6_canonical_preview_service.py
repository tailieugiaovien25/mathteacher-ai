from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assessment_generation_v2.services.assessment_curriculum_query_service import (
    AssessmentCurriculumTopic,
    AssessmentLearningRequirement,
)
from assessment_generation_v2.services.assessment_matrix_cell_authoring import (
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
from assessment_generation_v2.services.math6_canonical_preview_service import (
    Math6CanonicalMatrixSpecificationPreview,
    Math6CanonicalPreviewError,
    Math6CanonicalPreviewVariant,
    build_math6_canonical_matrix_specification_preview,
)
from assessment_generation_v2.services.math6_canonical_snapshot_bridge import (
    CanonicalRequirementCompetency,
    Math6CanonicalSnapshotIdentity,
)
from assessment_generation_v2.services.math6_mvp_workflow import (
    ADMIN,
    InMemoryMath6MvpWorkflow,
    Math6AssessmentConfig,
)


EXAM_VERSION_ID = "11111111-1111-4111-8111-111111111111"
BLUEPRINT_VERSION_ID = "22222222-2222-4222-8222-222222222222"
PUBLICATION_ID = "33333333-3333-4333-8333-333333333333"
VARIANT_ID = "44444444-4444-4444-8444-444444444444"


def _approved_blueprint():
    workflow = InMemoryMath6MvpWorkflow()
    config = Math6AssessmentConfig(
        config_code="M6-MIDTERM-PREVIEW",
        title="Canonical preview",
        academic_year="2026-2027",
        semester="HK1",
        test_type="MIDTERM",
        duration_minutes=90,
        total_score="10",
        variant_count=2,
    )
    workflow.create_blueprint(
        blueprint_code="M6-BP-PREVIEW",
        title="Math 6 canonical preview",
        assessment_config=config,
        question_count=20,
        total_score="10",
        topic_codes=("M6-LEGACY",),
    )
    workflow.bind_canonical_coverage(
        "M6-BP-PREVIEW",
        selection=CanonicalAssessmentSelection(
            subject_code="MATH",
            grade_level=6,
            program_code="CT2018-MATH",
            selected_topic_codes=("CURR-NODE-MATH-G6-003",),
            selected_requirement_codes=("YCCD-MATH-06-0001",),
            finalized=True,
        ),
        assignments=(
            BlueprintRequirementAssignment(
                requirement_code="YCCD-MATH-06-0001",
                coverage_role="PRIMARY",
                target_question_count=20,
                sequence_number=10,
                target_score="10",
                specification_note="Preview contract",
            ),
        ),
    )
    workflow.build_matrix_authoring(
        "M6-BP-PREVIEW",
        sections=(
            AssessmentProfileSectionOption(
                "MCQ",
                "Multiple choice",
                "MULTIPLE_CHOICE",
                10,
                12,
                12,
                "3",
            ),
            AssessmentProfileSectionOption(
                "TF",
                "True or false",
                "TRUE_FALSE",
                20,
                2,
                8,
                "2",
            ),
            AssessmentProfileSectionOption(
                "SHORT",
                "Short response",
                "SHORT_RESPONSE",
                30,
                4,
                4,
                "2",
            ),
            AssessmentProfileSectionOption(
                "ESSAY",
                "Essay",
                "ESSAY",
                40,
                2,
                2,
                "3",
            ),
        ),
        cognitive_levels=(
            CognitiveLevelOption("KNOW", "Recognition", 10),
            CognitiveLevelOption("UNDERSTAND", "Understanding", 20),
            CognitiveLevelOption("APPLY", "Application", 30),
        ),
        level_allocations=(
            ProfileLevelAllocation("KNOW", "4", "40"),
            ProfileLevelAllocation("UNDERSTAND", "3", "30"),
            ProfileLevelAllocation("APPLY", "3", "30"),
        ),
    )
    workflow.submit_blueprint("M6-BP-PREVIEW")
    return workflow.review_blueprint(
        "M6-BP-PREVIEW",
        role=ADMIN,
        approve=True,
    )


def _topic() -> AssessmentCurriculumTopic:
    return AssessmentCurriculumTopic(
        topic_code="CURR-NODE-MATH-G6-003",
        program_code="CT2018-MATH",
        parent_topic_code=None,
        grade_level=6,
        domain_code="NUMBER",
        topic_name="Numbers and algebra",
        sequence_number=30,
        status="ACTIVE",
        canonical_node_type="TOPIC",
    )


def _requirement() -> AssessmentLearningRequirement:
    return AssessmentLearningRequirement(
        requirement_code="YCCD-MATH-06-0001",
        program_code="CT2018-MATH",
        topic_code="CURR-NODE-MATH-G6-003",
        grade_level=6,
        requirement_text="Recognize a grade 6 mathematics requirement.",
        source_locator="CTGDPT 2018",
        version_number=1,
        status="ACTIVE",
        canonical_status="CANONICAL",
    )


def _identity() -> Math6CanonicalSnapshotIdentity:
    return Math6CanonicalSnapshotIdentity(
        publication_id=PUBLICATION_ID,
        published_at="2026-09-12T00:00:00Z",
        exam_version_id=EXAM_VERSION_ID,
        blueprint_version_id=BLUEPRINT_VERSION_ID,
        exam_title="Math 6 midterm",
        duration_minutes=90,
    )


def _variant() -> Math6CanonicalPreviewVariant:
    return Math6CanonicalPreviewVariant(
        variant_id=VARIANT_ID,
        variant_code="101",
        variant_hash="a" * 64,
    )


def _preview() -> Math6CanonicalMatrixSpecificationPreview:
    return build_math6_canonical_matrix_specification_preview(
        blueprint=_approved_blueprint(),
        snapshot_identity=_identity(),
        preview_variant=_variant(),
        topics=(_topic(),),
        requirements=(_requirement(),),
        question_type_names={
            "MULTIPLE_CHOICE": "Multiple choice",
            "TRUE_FALSE": "True or false",
            "SHORT_RESPONSE": "Short response",
            "ESSAY": "Essay",
        },
        competencies_by_requirement={
            "YCCD-MATH-06-0001": (
                CanonicalRequirementCompetency(
                    "MATH_REASONING",
                    "Mathematical reasoning",
                ),
            ),
        },
    )


def test_preview_returns_real_canonical_matrix_and_specification() -> None:
    preview = _preview()

    assert preview.snapshot_schema_version == 2
    assert len(preview.matrix) == 5
    assert len(preview.specification) == 1

    assert preview.matrix[0]["topic_name"] == "Numbers and algebra"
    assert preview.matrix[0]["domain_code"] == "NUMBER"
    assert preview.matrix[0]["cognitive_level_name"] == "Recognition"
    assert preview.matrix[0]["question_type_name"] == "Multiple choice"

    specification = preview.specification[0]
    assert specification["requirement_code"] == "YCCD-MATH-06-0001"
    assert specification["requirement_version_number"] == 1
    assert specification["source_locator"] == "CTGDPT 2018"
    assert specification["allocation_scope"] == "TOPIC"
    assert len(specification["topic_matrix_allocations"]) == 5
    assert specification["competencies"][0]["competency_code"] == (
        "MATH_REASONING"
    )


def test_preview_preserves_canonical_builder_metadata() -> None:
    preview = _preview()

    assert preview.metadata["snapshot_schema_version"] == 2
    assert preview.metadata["canonical_schema_version"] == 1
    assert preview.metadata["exam"]["exam_version_id"] == EXAM_VERSION_ID
    assert preview.metadata["variant"]["variant_id"] == VARIANT_ID
    assert preview.metadata["totals"]["matrix_cell_count"] == 5
    assert preview.metadata["totals"]["requirement_count"] == 1


def test_preview_requires_caller_owned_variant_identity() -> None:
    with pytest.raises(
        Math6CanonicalPreviewError,
        match="valid UUID",
    ):
        Math6CanonicalPreviewVariant(
            variant_id="not-a-uuid",
            variant_code="101",
            variant_hash="a" * 64,
        )


def test_preview_rejects_non_sha256_variant_hash() -> None:
    with pytest.raises(
        Math6CanonicalPreviewError,
        match="SHA-256",
    ):
        Math6CanonicalPreviewVariant(
            variant_id=VARIANT_ID,
            variant_code="101",
            variant_hash="abc",
        )


def test_preview_service_does_not_mutate_publish_state() -> None:
    blueprint = _approved_blueprint()

    preview = build_math6_canonical_matrix_specification_preview(
        blueprint=blueprint,
        snapshot_identity=_identity(),
        preview_variant=_variant(),
        topics=(_topic(),),
        requirements=(_requirement(),),
        question_type_names={
            "MULTIPLE_CHOICE": "Multiple choice",
            "TRUE_FALSE": "True or false",
            "SHORT_RESPONSE": "Short response",
            "ESSAY": "Essay",
        },
    )

    assert preview.snapshot_schema_version == 2
    assert blueprint.review_status == "APPROVED"
    assert blueprint.locked is True
