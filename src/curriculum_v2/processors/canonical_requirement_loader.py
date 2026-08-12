import json
from pathlib import Path

from curriculum_v2.models import (
    CanonicalLearningRequirement,
    RequirementProvenance,
    RequirementValidation,
)


def load_canonical_requirements(
    file_path: str | Path,
) -> list[CanonicalLearningRequirement]:
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    requirements = []

    for item in data["requirements"]:
        provenance_data = item["provenance"]
        validation_data = item["validation"]

        provenance = RequirementProvenance(
            legal_authority=provenance_data["legal_authority"],
            regulation_id=provenance_data["regulation_id"],
            source_document_id=provenance_data["source_document_id"],
            verified_copy_id=provenance_data.get("verified_copy_id"),
            source_location=provenance_data.get("source_location"),
            source_version=provenance_data.get("source_version"),
        )

        validation = RequirementValidation(
            text_integrity=validation_data["text_integrity"],
            structural_integrity=validation_data["structural_integrity"],
            provenance_integrity=validation_data["provenance_integrity"],
            identity_integrity=validation_data["identity_integrity"],
        )

        requirement = CanonicalLearningRequirement(
            canonical_id=item["canonical_id"],
            curriculum_ref=data["curriculum_ref"],
            curriculum_node_ref=item["curriculum_node_ref"],
            requirement_text_original=item[
                "requirement_text_original"
            ],
            provenance=provenance,
            validation=validation,
            status=item.get("status", "CANDIDATE"),
            schema_version=data.get("schema_version", 4),
        )

        requirements.append(requirement)

    return requirements