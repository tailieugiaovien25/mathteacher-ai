import json
from pathlib import Path

from curriculum_v2.models import CanonicalLearningRequirement
from curriculum_v2.processors.canonical_requirement_loader import (
    load_canonical_requirements,
)
from curriculum_v2.rules import can_be_verified


DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "canonical"
    / "mathematics"
    / "grade_06"
    / "learning_requirements.json"
)


def load_raw_data() -> dict:
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def test_loader_returns_all_canonical_requirement_objects():
    raw_data = load_raw_data()
    requirements = load_canonical_requirements(DATA_FILE)

    assert len(requirements) == len(raw_data["requirements"])

    assert all(
        isinstance(
            requirement,
            CanonicalLearningRequirement,
        )
        for requirement in requirements
    )


def test_loader_preserves_identity_and_context():
    requirement = load_canonical_requirements(DATA_FILE)[0]

    assert requirement.canonical_id == "YCCD-MATH-06-0001"
    assert requirement.curriculum_ref == "CURRICULUM-MATH-2018"
    assert requirement.curriculum_node_ref == (
        "CURR-NODE-MATH-G6-004"
    )


def test_loader_preserves_provenance():
    requirement = load_canonical_requirements(DATA_FILE)[0]

    assert requirement.provenance.legal_authority == (
        "Bộ Giáo dục và Đào tạo"
    )

    assert requirement.provenance.regulation_id == (
        "32/2018/TT-BGDĐT"
    )

    assert requirement.provenance.source_document_id == (
        "SRC-CUR-MATH-2018"
    )


def test_loaded_requirements_can_be_verified():
    requirements = load_canonical_requirements(DATA_FILE)

    assert requirements

    assert all(
        requirement.status == "VERIFIED"
        for requirement in requirements
    )

    assert all(
        can_be_verified(requirement)
        for requirement in requirements
    )


def test_loaded_canonical_ids_are_unique():
    requirements = load_canonical_requirements(DATA_FILE)

    canonical_ids = [
        requirement.canonical_id
        for requirement in requirements
    ]

    assert len(canonical_ids) == len(set(canonical_ids))