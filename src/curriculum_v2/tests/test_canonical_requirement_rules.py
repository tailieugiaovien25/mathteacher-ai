from curriculum_v2.models.canonical_learning_requirement import (
    CanonicalLearningRequirement,
    RequirementProvenance,
    RequirementValidation,
)
from curriculum_v2.rules.canonical_requirement_rules import (
    can_be_verified,
    is_validation_complete,
    is_verified_consistent,
)


def make_provenance() -> RequirementProvenance:
    return RequirementProvenance(
        legal_authority="MOET",
        regulation_id="32/2018/TT-BGDĐT",
        source_document_id="SRC-CUR-MATH-2018",
    )


def test_all_validation_gates_pass():
    requirement = CanonicalLearningRequirement(
        canonical_id="YCCD-MATH-06-0001",
        curriculum_ref="CURRICULUM-MATH-2018",
        curriculum_node_ref="CURR-NODE-MATH-G6-001",
        requirement_text_original="Sample requirement.",
        provenance=make_provenance(),
        validation=RequirementValidation(
            text_integrity="PASS",
            structural_integrity="PASS",
            provenance_integrity="PASS",
            identity_integrity="PASS",
        ),
    )

    assert is_validation_complete(requirement) is True
    assert can_be_verified(requirement) is True


def test_one_failed_gate_blocks_verification():
    requirement = CanonicalLearningRequirement(
        canonical_id="YCCD-MATH-06-0002",
        curriculum_ref="CURRICULUM-MATH-2018",
        curriculum_node_ref="CURR-NODE-MATH-G6-001",
        requirement_text_original="Sample requirement.",
        provenance=make_provenance(),
        validation=RequirementValidation(
            text_integrity="PASS",
            structural_integrity="PASS",
            provenance_integrity="PENDING",
            identity_integrity="PASS",
        ),
    )

    assert is_validation_complete(requirement) is False
    assert can_be_verified(requirement) is False


def test_verified_status_requires_all_gates_pass():
    requirement = CanonicalLearningRequirement(
        canonical_id="YCCD-MATH-06-0003",
        curriculum_ref="CURRICULUM-MATH-2018",
        curriculum_node_ref="CURR-NODE-MATH-G6-001",
        requirement_text_original="Sample requirement.",
        provenance=make_provenance(),
        validation=RequirementValidation(
            text_integrity="PASS",
            structural_integrity="PASS",
            provenance_integrity="PENDING",
            identity_integrity="PASS",
        ),
        status="VERIFIED",
    )

    assert is_verified_consistent(requirement) is False


def test_candidate_status_can_remain_incomplete():
    requirement = CanonicalLearningRequirement(
        canonical_id="YCCD-MATH-06-0004",
        curriculum_ref="CURRICULUM-MATH-2018",
        curriculum_node_ref="CURR-NODE-MATH-G6-001",
        requirement_text_original="Sample requirement.",
        provenance=make_provenance(),
        validation=RequirementValidation(
            text_integrity="PENDING",
            structural_integrity="PENDING",
            provenance_integrity="PENDING",
            identity_integrity="PENDING",
        ),
    )

    assert is_verified_consistent(requirement) is True