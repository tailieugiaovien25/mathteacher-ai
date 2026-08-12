from curriculum_v2.models.canonical_learning_requirement import (
    CanonicalLearningRequirement,
)


REQUIRED_VALIDATION_STATUS = "PASS"
VERIFIED_STATUS = "VERIFIED"


def is_validation_complete(
    requirement: CanonicalLearningRequirement,
) -> bool:
    validation = requirement.validation

    return all(
        value == REQUIRED_VALIDATION_STATUS
        for value in (
            validation.text_integrity,
            validation.structural_integrity,
            validation.provenance_integrity,
            validation.identity_integrity,
        )
    )


def can_be_verified(
    requirement: CanonicalLearningRequirement,
) -> bool:
    return is_validation_complete(requirement)


def is_verified_consistent(
    requirement: CanonicalLearningRequirement,
) -> bool:
    if requirement.status != VERIFIED_STATUS:
        return True

    return can_be_verified(requirement)