from dataclasses import dataclass


@dataclass(frozen=True)
class RequirementProvenance:
    legal_authority: str
    regulation_id: str
    source_document_id: str

    verified_copy_id: str | None = None
    source_location: str | None = None
    source_version: str | None = None


@dataclass(frozen=True)
class RequirementValidation:
    text_integrity: str
    structural_integrity: str
    provenance_integrity: str
    identity_integrity: str


@dataclass(frozen=True)
class CanonicalLearningRequirement:
    canonical_id: str

    curriculum_ref: str
    curriculum_node_ref: str

    requirement_text_original: str

    provenance: RequirementProvenance
    validation: RequirementValidation

    status: str = "CANDIDATE"
    schema_version: int = 4