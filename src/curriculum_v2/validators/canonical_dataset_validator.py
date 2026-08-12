import json
from pathlib import Path

from curriculum_v2.processors.canonical_requirement_loader import (
    load_canonical_requirements,
)
from curriculum_v2.rules import is_verified_consistent


EXPECTED_SCHEMA_VERSION = 4


def load_json(path: str | Path) -> dict:
    path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_canonical_dataset(
    requirements_file: str | Path,
    nodes_file: str | Path,
    source_file: str | Path,
) -> list[str]:
    errors: list[str] = []

    requirements_data = load_json(requirements_file)
    nodes_data = load_json(nodes_file)
    source_data = load_json(source_file)

    requirements = load_canonical_requirements(
        requirements_file
    )

    # 1. Dataset schema version
    if requirements_data.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        errors.append("INVALID_SCHEMA_VERSION")

    # 2. Canonical IDs must be unique
    canonical_ids = [
        requirement.canonical_id
        for requirement in requirements
    ]

    if len(canonical_ids) != len(set(canonical_ids)):
        errors.append("DUPLICATE_CANONICAL_ID")

    # 3. Referenced curriculum nodes must exist
    node_ids = {
        node["curriculum_node_id"]
        for node in nodes_data["nodes"]
    }

    for requirement in requirements:
        if requirement.curriculum_node_ref not in node_ids:
            errors.append(
                f"UNKNOWN_CURRICULUM_NODE:"
                f"{requirement.canonical_id}"
            )

    # 4. Provenance source must match registered source
    registered_source_id = source_data["source_id"]

    for requirement in requirements:
        if (
            requirement.provenance.source_document_id
            != registered_source_id
        ):
            errors.append(
                f"UNKNOWN_SOURCE:"
                f"{requirement.canonical_id}"
            )

    # 5. Requirement text must not be empty
    for requirement in requirements:
        if not requirement.requirement_text_original.strip():
            errors.append(
                f"EMPTY_REQUIREMENT_TEXT:"
                f"{requirement.canonical_id}"
            )

    # 6. VERIFIED records must satisfy validation rules
    for requirement in requirements:
        if not is_verified_consistent(requirement):
            errors.append(
                f"INVALID_VERIFIED_STATUS:"
                f"{requirement.canonical_id}"
            )

    return errors