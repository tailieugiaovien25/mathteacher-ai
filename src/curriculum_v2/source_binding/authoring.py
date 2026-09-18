"""Governed authoring for source-to-canonical binding data.

Runtime resolution stays deterministic and strict. This authoring service is
the separate place where a reviewer (or a future AI-assisted workbench) may
propose a mapping. Proposals are CANDIDATE data only; they become VERIFIED
only through an explicit verifier action.

This separation is intentional:
- runtime never guesses,
- AI may assist authoring later but cannot self-verify,
- source changes create new data/versioned bindings, not code changes.
"""

from __future__ import annotations

import json
from dataclasses import replace

from .json_loader import (
    SourceCanonicalBindingDataset,
    SourceCanonicalBindingJsonLoader,
)
from .models import (
    CurriculumSourceItem,
    SourceCanonicalBinding,
    SourceCanonicalBindingProvenance,
)


class SourceCanonicalBindingAuthoringError(
    ValueError
):
    """Raised when a governed authoring transition is invalid."""


def _required_text(
    value: object,
    field: str,
) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise SourceCanonicalBindingAuthoringError(
            f"{field} must not be empty"
        )
    return normalized


class SourceCanonicalBindingAuthoringService:
    """Create and govern mapping data without runtime inference."""

    def create_candidate(
        self,
        *,
        binding_id: str,
        item: CurriculumSourceItem,
        canonical_lesson_id: str,
        source_document_id: str,
        mapping_method: str,
        source_location: str | None = None,
    ) -> SourceCanonicalBinding:
        if not isinstance(
            item,
            CurriculumSourceItem,
        ):
            raise TypeError(
                "item must be CurriculumSourceItem"
            )

        location = (
            str(source_location).strip()
            if source_location is not None
            and str(source_location).strip()
            else item.source_location
        )

        provenance = (
            SourceCanonicalBindingProvenance(
                source_document_id=_required_text(
                    source_document_id,
                    "source_document_id",
                ),
                mapping_method=_required_text(
                    mapping_method,
                    "mapping_method",
                ),
                verified_by=None,
                source_location=location,
                source_version=(
                    item.source_version
                ),
            )
        )

        return SourceCanonicalBinding(
            binding_id=_required_text(
                binding_id,
                "binding_id",
            ),
            source_type=item.source_type,
            source_id=item.source_id,
            source_version=item.source_version,
            academic_year=item.academic_year,
            subject_code=item.subject_code,
            grade_level=item.grade_level,
            external_item_key=(
                item.external_item_key
            ),
            canonical_lesson_id=(
                _required_text(
                    canonical_lesson_id,
                    "canonical_lesson_id",
                )
            ),
            provenance=provenance,
            status="CANDIDATE",
            schema_version=1,
        )

    def verify(
        self,
        *,
        binding: SourceCanonicalBinding,
        verified_by: str,
    ) -> SourceCanonicalBinding:
        self._binding(binding)

        if binding.status != "CANDIDATE":
            raise SourceCanonicalBindingAuthoringError(
                "only CANDIDATE bindings may be VERIFIED"
            )

        verifier = _required_text(
            verified_by,
            "verified_by",
        )

        provenance = replace(
            binding.provenance,
            verified_by=verifier,
        )

        return replace(
            binding,
            provenance=provenance,
            status="VERIFIED",
        )

    def deprecate(
        self,
        *,
        binding: SourceCanonicalBinding,
    ) -> SourceCanonicalBinding:
        self._binding(binding)

        if binding.status == "DEPRECATED":
            raise SourceCanonicalBindingAuthoringError(
                "binding is already DEPRECATED"
            )

        return replace(
            binding,
            status="DEPRECATED",
        )

    @staticmethod
    def _binding(
        binding: SourceCanonicalBinding,
    ) -> None:
        if not isinstance(
            binding,
            SourceCanonicalBinding,
        ):
            raise TypeError(
                "binding must be SourceCanonicalBinding"
            )


class SourceCanonicalBindingDatasetWriter:
    """Deterministic JSON writer compatible with the strict loader."""

    def __init__(
        self,
        *,
        loader: SourceCanonicalBindingJsonLoader
        | None = None,
    ) -> None:
        self._loader = (
            loader
            or SourceCanonicalBindingJsonLoader()
        )

    def build_dataset(
        self,
        *,
        dataset_id: str,
        bindings: tuple[
            SourceCanonicalBinding,
            ...,
        ],
    ) -> SourceCanonicalBindingDataset:
        payload = {
            "dataset_id": _required_text(
                dataset_id,
                "dataset_id",
            ),
            "schema_version": 1,
            "bindings": [
                self._binding_payload(binding)
                for binding in bindings
            ],
        }

        return self._loader.load_payload(
            payload
        )

    def dumps(
        self,
        *,
        dataset_id: str,
        bindings: tuple[
            SourceCanonicalBinding,
            ...,
        ],
    ) -> str:
        dataset = self.build_dataset(
            dataset_id=dataset_id,
            bindings=bindings,
        )

        payload = {
            "dataset_id": dataset.dataset_id,
            "schema_version": (
                dataset.schema_version
            ),
            "bindings": [
                self._binding_payload(binding)
                for binding in dataset.bindings
            ],
        }

        return (
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=False,
            )
            + "\n"
        )

    @staticmethod
    def _binding_payload(
        binding: SourceCanonicalBinding,
    ) -> dict[str, object]:
        if not isinstance(
            binding,
            SourceCanonicalBinding,
        ):
            raise TypeError(
                "bindings must contain "
                "SourceCanonicalBinding values"
            )

        provenance = binding.provenance

        return {
            "binding_id": binding.binding_id,
            "source_type": binding.source_type,
            "source_id": binding.source_id,
            "source_version": (
                binding.source_version
            ),
            "academic_year": (
                binding.academic_year
            ),
            "subject_code": (
                binding.subject_code
            ),
            "grade_level": binding.grade_level,
            "external_item_key": (
                binding.external_item_key
            ),
            "canonical_lesson_id": (
                binding.canonical_lesson_id
            ),
            "provenance": {
                "source_document_id": (
                    provenance.source_document_id
                ),
                "mapping_method": (
                    provenance.mapping_method
                ),
                "verified_by": (
                    provenance.verified_by
                ),
                "source_location": (
                    provenance.source_location
                ),
                "source_version": (
                    provenance.source_version
                ),
            },
            "status": binding.status,
            "schema_version": (
                binding.schema_version
            ),
        }
