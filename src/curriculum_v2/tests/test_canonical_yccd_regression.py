from pathlib import Path

from curriculum_v2.models import CanonicalLearningRequirement
from curriculum_v2.processors import load_canonical_requirements
from curriculum_v2.rules import (
    can_be_verified,
    is_verified_consistent,
)
from curriculum_v2.validators import (
    validate_canonical_dataset,
)


BASE_DIR = Path(__file__).resolve().parents[1]

SOURCE_FILE = (
    BASE_DIR
    / "data"
    / "sources"
    / "SRC-CUR-MATH-2018.json"
)

NODES_FILE = (
    BASE_DIR
    / "data"
    / "canonical"
    / "mathematics"
    / "grade_06"
    / "curriculum_nodes.json"
)

REQUIREMENTS_FILE = (
    BASE_DIR
    / "data"
    / "canonical"
    / "mathematics"
    / "grade_06"
    / "learning_requirements.json"
)


def test_canonical_yccd_pipeline_is_healthy():
    assert SOURCE_FILE.exists()
    assert NODES_FILE.exists()
    assert REQUIREMENTS_FILE.exists()

    errors = validate_canonical_dataset(
        REQUIREMENTS_FILE,
        NODES_FILE,
        SOURCE_FILE,
    )

    assert errors == []

    requirements = load_canonical_requirements(
        REQUIREMENTS_FILE
    )

    assert len(requirements) >= 1

    assert all(
        isinstance(
            requirement,
            CanonicalLearningRequirement,
        )
        for requirement in requirements
    )

    assert all(
        requirement.status == "VERIFIED"
        for requirement in requirements
    )

    assert all(
        can_be_verified(requirement)
        for requirement in requirements
    )

    assert all(
        is_verified_consistent(requirement)
        for requirement in requirements
    )


def test_canonical_yccd_ids_are_unique():
    requirements = load_canonical_requirements(
        REQUIREMENTS_FILE
    )

    canonical_ids = [
        requirement.canonical_id
        for requirement in requirements
    ]

    assert len(canonical_ids) == len(set(canonical_ids))


def test_canonical_yccd_provenance_is_consistent():
    requirements = load_canonical_requirements(
        REQUIREMENTS_FILE
    )

    assert all(
        requirement.provenance.source_document_id
        == "SRC-CUR-MATH-2018"
        for requirement in requirements
    )

    assert all(
        requirement.provenance.regulation_id
        == "32/2018/TT-BGDĐT"
        for requirement in requirements
    )