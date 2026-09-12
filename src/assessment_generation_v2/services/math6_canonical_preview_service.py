"""Math 6 canonical matrix/specification preview runtime.

This module is deliberately in-memory and non-governed:
it does not publish, persist, export DOCX, call Supabase, or create IDs.
All governed identifiers must be supplied by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence
from uuid import UUID

from assessment_generation_v2.documents import (
    CanonicalAssessmentDocumentBuilder,
)
from assessment_generation_v2.services.assessment_curriculum_query_service import (
    AssessmentCurriculumTopic,
    AssessmentLearningRequirement,
)
from assessment_generation_v2.services.math6_canonical_snapshot_bridge import (
    CanonicalRequirementCompetency,
    Math6CanonicalBlueprintLike,
    Math6CanonicalSnapshotIdentity,
    build_math6_canonical_snapshot,
)


class Math6CanonicalPreviewError(ValueError):
    """Raised when a canonical preview request is invalid."""


def _text(value: object, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise Math6CanonicalPreviewError(f"{field_name} is required")
    return normalized


def _uuid(value: object, field_name: str) -> str:
    text = _text(value, field_name)
    try:
        return str(UUID(text))
    except ValueError as error:
        raise Math6CanonicalPreviewError(
            f"{field_name} must be a valid UUID"
        ) from error


def _sha256(value: object, field_name: str) -> str:
    text = _text(value, field_name).lower()
    if len(text) != 64 or any(
        character not in "0123456789abcdef"
        for character in text
    ):
        raise Math6CanonicalPreviewError(
            f"{field_name} must be a SHA-256 hex digest"
        )
    return text


def _freeze_mapping(
    value: Mapping[str, object],
) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class Math6CanonicalPreviewVariant:
    """Caller-owned immutable variant identity for preview only."""

    variant_id: str
    variant_code: str
    variant_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "variant_id",
            _uuid(self.variant_id, "variant_id"),
        )
        object.__setattr__(
            self,
            "variant_code",
            _text(self.variant_code, "variant_code").upper(),
        )
        object.__setattr__(
            self,
            "variant_hash",
            _sha256(self.variant_hash, "variant_hash"),
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "variant_id": self.variant_id,
            "variant_code": self.variant_code,
            "variant_hash": self.variant_hash,
        }


@dataclass(frozen=True, slots=True)
class Math6CanonicalMatrixSpecificationPreview:
    """Frozen canonical matrix/specification produced from schema 2 data."""

    snapshot_schema_version: int
    metadata: Mapping[str, object]
    matrix: tuple[Mapping[str, object], ...]
    specification: tuple[Mapping[str, object], ...]

    def __post_init__(self) -> None:
        if self.snapshot_schema_version != 2:
            raise Math6CanonicalPreviewError(
                "snapshot schema 2 preview is required"
            )
        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata),
        )


def build_math6_canonical_matrix_specification_preview(
    *,
    blueprint: Math6CanonicalBlueprintLike,
    snapshot_identity: Math6CanonicalSnapshotIdentity,
    preview_variant: Math6CanonicalPreviewVariant,
    topics: Sequence[AssessmentCurriculumTopic],
    requirements: Sequence[AssessmentLearningRequirement],
    question_type_names: Mapping[str, str],
    competencies_by_requirement: Mapping[
        str,
        Sequence[CanonicalRequirementCompetency],
    ] | None = None,
) -> Math6CanonicalMatrixSpecificationPreview:
    """Build real canonical matrix/specification without publish or export."""

    if not isinstance(
        snapshot_identity,
        Math6CanonicalSnapshotIdentity,
    ):
        raise Math6CanonicalPreviewError(
            "snapshot_identity must be Math6CanonicalSnapshotIdentity"
        )
    if not isinstance(
        preview_variant,
        Math6CanonicalPreviewVariant,
    ):
        raise Math6CanonicalPreviewError(
            "preview_variant must be Math6CanonicalPreviewVariant"
        )

    snapshot = build_math6_canonical_snapshot(
        blueprint=blueprint,
        identity=snapshot_identity,
        topics=topics,
        requirements=requirements,
        question_type_names=question_type_names,
        competencies_by_requirement=competencies_by_requirement,
    )

    exam = dict(snapshot["exam"])
    variant = preview_variant.as_payload()

    student_payload = {
        "package_schema_version": 1,
        "package_type": "STUDENT_EXAM",
        "variant": dict(variant),
        "exam": dict(exam),
        "questions": [],
    }
    answer_payload = {
        "package_schema_version": 1,
        "package_type": "ANSWER_KEY",
        "variant": dict(variant),
        "exam": dict(exam),
        "answers": [],
    }
    scoring_payload = {
        "package_schema_version": 1,
        "package_type": "SCORING_GUIDE",
        "variant": dict(variant),
        "exam": dict(exam),
        "scoring_items": [],
    }

    document = CanonicalAssessmentDocumentBuilder().build(
        snapshot_document=snapshot,
        student_exam_payload=student_payload,
        answer_key_payload=answer_payload,
        scoring_guide_payload=scoring_payload,
    )

    return Math6CanonicalMatrixSpecificationPreview(
        snapshot_schema_version=2,
        metadata=document.metadata,
        matrix=document.matrix,
        specification=document.specification,
    )
