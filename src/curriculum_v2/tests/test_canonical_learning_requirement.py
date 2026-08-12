from curriculum_v2.models.canonical_learning_requirement import (
    CanonicalLearningRequirement,
    RequirementProvenance,
    RequirementValidation,
)


def test_canonical_learning_requirement_creation():
    provenance = RequirementProvenance(
        legal_authority="MOET",
        regulation_id="32/2018/TT-BGDĐT",
        source_document_id="SRC-CUR-MATH-2018",
        verified_copy_id="VERIFIED-COPY-001",
        source_location="Grade 6",
        source_version="2018",
    )

    validation = RequirementValidation(
        text_integrity="PASS",
        structural_integrity="PASS",
        provenance_integrity="PASS",
        identity_integrity="PASS",
    )

    requirement = CanonicalLearningRequirement(
        canonical_id="YCCD-MATH-06-0001",
        curriculum_ref="CURRICULUM-MATH-2018",
        curriculum_node_ref="CURR-NODE-MATH-G6-001",
        requirement_text_original="Sample official requirement text.",
        provenance=provenance,
        validation=validation,
        status="VERIFIED",
    )

    assert requirement.canonical_id == "YCCD-MATH-06-0001"
    assert requirement.curriculum_ref == "CURRICULUM-MATH-2018"
    assert requirement.curriculum_node_ref == "CURR-NODE-MATH-G6-001"

    assert requirement.requirement_text_original == (
        "Sample official requirement text."
    )

    assert requirement.provenance.regulation_id == "32/2018/TT-BGDĐT"
    assert requirement.validation.text_integrity == "PASS"

    assert requirement.status == "VERIFIED"
    assert requirement.schema_version == 4


def test_default_status_is_candidate():
    provenance = RequirementProvenance(
        legal_authority="MOET",
        regulation_id="32/2018/TT-BGDĐT",
        source_document_id="SRC-CUR-MATH-2018",
    )

    validation = RequirementValidation(
        text_integrity="PENDING",
        structural_integrity="PENDING",
        provenance_integrity="PENDING",
        identity_integrity="PENDING",
    )

    requirement = CanonicalLearningRequirement(
        canonical_id="YCCD-MATH-06-0002",
        curriculum_ref="CURRICULUM-MATH-2018",
        curriculum_node_ref="CURR-NODE-MATH-G6-001",
        requirement_text_original="Another sample requirement.",
        provenance=provenance,
        validation=validation,
    )

    assert requirement.status == "CANDIDATE"