from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assessment_generation_v2.documents import (
    CanonicalAssessmentDocumentBuilder,
)
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
from assessment_generation_v2.services.math6_canonical_snapshot_bridge import (
    CanonicalRequirementCompetency,
    Math6CanonicalSnapshotBridgeError,
    Math6CanonicalSnapshotIdentity,
    build_math6_canonical_snapshot,
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
        config_code="M6-MIDTERM-CANONICAL-BRIDGE",
        title="Math 6 canonical bridge",
        academic_year="2026-2027",
        semester="HK1",
        test_type="MIDTERM",
        duration_minutes=90,
        total_score="10",
        variant_count=2,
    )
    workflow.create_blueprint(
        blueprint_code="M6-BP-CANONICAL-BRIDGE",
        title="Math 6 canonical matrix",
        assessment_config=config,
        question_count=20,
        total_score="10",
        topic_codes=("M6-LEGACY",),
    )
    selection = CanonicalAssessmentSelection(
        subject_code="MATH",
        grade_level=6,
        program_code="CT2018-MATH",
        selected_topic_codes=("CURR-NODE-MATH-G6-003",),
        selected_requirement_codes=("YCCD-MATH-06-0001",),
        finalized=True,
    )
    workflow.bind_canonical_coverage(
        "M6-BP-CANONICAL-BRIDGE",
        selection=selection,
        assignments=(
            BlueprintRequirementAssignment(
                requirement_code="YCCD-MATH-06-0001",
                coverage_role="PRIMARY",
                target_question_count=20,
                sequence_number=10,
                target_score="10",
                specification_note="Canonical bridge",
            ),
        ),
    )
    workflow.build_matrix_authoring(
        "M6-BP-CANONICAL-BRIDGE",
        sections=(
            AssessmentProfileSectionOption(
                "MCQ", "Multiple choice", "MULTIPLE_CHOICE",
                10, 12, 12, "3",
            ),
            AssessmentProfileSectionOption(
                "TF", "True or false", "TRUE_FALSE",
                20, 2, 8, "2",
            ),
            AssessmentProfileSectionOption(
                "SHORT", "Short response", "SHORT_RESPONSE",
                30, 4, 4, "2",
            ),
            AssessmentProfileSectionOption(
                "ESSAY", "Essay", "ESSAY",
                40, 2, 2, "3",
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
    workflow.submit_blueprint("M6-BP-CANONICAL-BRIDGE")
    return workflow.review_blueprint(
        "M6-BP-CANONICAL-BRIDGE",
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
        published_at="2026-09-11T00:00:00Z",
        exam_version_id=EXAM_VERSION_ID,
        blueprint_version_id=BLUEPRINT_VERSION_ID,
        exam_title="Math 6 midterm",
        duration_minutes=90,
    )


def _snapshot():
    return build_math6_canonical_snapshot(
        blueprint=_approved_blueprint(),
        identity=_identity(),
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


def _package(package_type: str) -> dict[str, object]:
    snapshot = _snapshot()
    base = {
        "package_schema_version": 1,
        "package_type": package_type,
        "variant": {
            "variant_id": VARIANT_ID,
            "variant_code": "101",
            "variant_hash": "a" * 64,
        },
        "exam": dict(snapshot["exam"]),
    }
    if package_type == "STUDENT_EXAM":
        base["questions"] = []
    elif package_type == "ANSWER_KEY":
        base["answers"] = []
    else:
        base["scoring_items"] = []
    return base


def test_bridge_builds_snapshot_schema_two_with_frozen_labels() -> None:
    snapshot = _snapshot()

    assert snapshot["snapshot_schema_version"] == 2
    assert snapshot["publication"]["publication_id"] == PUBLICATION_ID
    assert snapshot["exam"]["exam_version_id"] == EXAM_VERSION_ID
    assert snapshot["blueprint"]["blueprint_version_id"] == (
        BLUEPRINT_VERSION_ID
    )

    blueprint = snapshot["blueprint"]
    assert len(blueprint["sections"]) == 4
    assert len(blueprint["matrix_cells"]) == 5
    assert len(blueprint["requirement_links"]) == 1

    first_cell = blueprint["matrix_cells"][0]
    assert first_cell["topic_name"] == "Numbers and algebra"
    assert first_cell["domain_code"] == "NUMBER"
    assert first_cell["cognitive_level_name"] == "Recognition"
    assert first_cell["question_type_name"] == "Multiple choice"
    assert "blueprint_cell_id" not in first_cell

    requirement = blueprint["requirement_links"][0]
    assert requirement["requirement_version_number"] == 1
    assert requirement["source_locator"] == "CTGDPT 2018"
    assert requirement["competencies"][0]["competency_code"] == (
        "MATH_REASONING"
    )


def test_bridge_snapshot_is_consumed_by_canonical_document_builder() -> None:
    document = CanonicalAssessmentDocumentBuilder().build(
        snapshot_document=_snapshot(),
        student_exam_payload=_package("STUDENT_EXAM"),
        answer_key_payload=_package("ANSWER_KEY"),
        scoring_guide_payload=_package("SCORING_GUIDE"),
    )

    assert len(document.matrix) == 5
    assert len(document.specification) == 1
    assert document.metadata["snapshot_schema_version"] == 2
    assert document.matrix[0]["topic_name"] == "Numbers and algebra"
    assert document.specification[0]["allocation_scope"] == "TOPIC"
    assert len(
        document.specification[0]["topic_matrix_allocations"]
    ) == 5


def test_bridge_requires_approved_locked_blueprint() -> None:
    workflow = InMemoryMath6MvpWorkflow()
    config = Math6AssessmentConfig(
        config_code="M6-BRIDGE-DRAFT",
        title="Draft",
        academic_year="2026-2027",
        semester="HK1",
        test_type="MIDTERM",
        duration_minutes=90,
        total_score="10",
        variant_count=1,
    )
    draft = workflow.create_blueprint(
        blueprint_code="M6-BP-DRAFT",
        title="Draft",
        assessment_config=config,
        question_count=20,
        total_score="10",
        topic_codes=("M6-LEGACY",),
    )

    try:
        build_math6_canonical_snapshot(
            blueprint=draft,
            identity=_identity(),
            topics=(_topic(),),
            requirements=(_requirement(),),
            question_type_names={},
        )
    except Math6CanonicalSnapshotBridgeError as error:
        assert "approved locked blueprint" in str(error)
    else:
        raise AssertionError("draft blueprint unexpectedly accepted")


def test_bridge_never_fabricates_governed_identifiers() -> None:
    snapshot = _snapshot()

    assert "variant" not in snapshot
    assert "variant_id" not in snapshot
    assert all(
        "blueprint_cell_id" not in row
        for row in snapshot["blueprint"]["matrix_cells"]
    )
