from curriculum_v2.models import (
    CanonicalLearningRequirement,
    RequirementProvenance,
    RequirementValidation,
)
from curriculum_v2.rules import (
    can_be_verified,
    is_validation_complete,
    is_verified_consistent,
)


def test_canonical_models_are_publicly_exported():
    assert CanonicalLearningRequirement is not None
    assert RequirementProvenance is not None
    assert RequirementValidation is not None


def test_canonical_rules_are_publicly_exported():
    assert can_be_verified is not None
    assert is_validation_complete is not None
    assert is_verified_consistent is not None