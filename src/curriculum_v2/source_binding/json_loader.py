"""Versioned JSON loader for source-to-canonical binding data.

This module keeps mapping decisions in data rather than Python code.
Changing source versions, periods, external keys, or canonical targets only
requires replacing the binding dataset, provided the stable schema remains
compatible.

The loader is intentionally strict and fail-closed:
- schema_version must be supported,
- unknown fields are rejected,
- every record is validated through SourceCanonicalBinding,
- duplicate binding_id values are rejected,
- duplicate exact VERIFIED identities are rejected before runtime,
- no fuzzy matching or canonical inference occurs while loading.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import (
    SourceCanonicalBinding,
    SourceCanonicalBindingProvenance,
)


class SourceCanonicalBindingDataError(ValueError):
    """Raised when a binding dataset is invalid or unsafe."""


@dataclass(frozen=True, slots=True)
class SourceCanonicalBindingDataset:
    dataset_id: str
    schema_version: int
    bindings: tuple[SourceCanonicalBinding, ...]

    def __post_init__(self) -> None:
        dataset_id = str(self.dataset_id or "").strip()
        if not dataset_id:
            raise SourceCanonicalBindingDataError(
                "dataset_id must not be empty"
            )
        object.__setattr__(
            self,
            "dataset_id",
            dataset_id,
        )

        if isinstance(self.schema_version, bool):
            raise SourceCanonicalBindingDataError(
                "schema_version must be a positive integer"
            )

        try:
            schema_version = int(self.schema_version)
        except (TypeError, ValueError) as error:
            raise SourceCanonicalBindingDataError(
                "schema_version must be a positive integer"
            ) from error

        if schema_version < 1:
            raise SourceCanonicalBindingDataError(
                "schema_version must be a positive integer"
            )

        object.__setattr__(
            self,
            "schema_version",
            schema_version,
        )

        if not isinstance(self.bindings, tuple):
            raise SourceCanonicalBindingDataError(
                "bindings must be a tuple"
            )

        if any(
            not isinstance(
                item,
                SourceCanonicalBinding,
            )
            for item in self.bindings
        ):
            raise SourceCanonicalBindingDataError(
                "bindings must contain "
                "SourceCanonicalBinding values"
            )


class SourceCanonicalBindingJsonLoader:
    SUPPORTED_SCHEMA_VERSIONS = frozenset({1})

    _ROOT_KEYS = frozenset(
        {
            "dataset_id",
            "schema_version",
            "bindings",
        }
    )

    _BINDING_KEYS = frozenset(
        {
            "binding_id",
            "source_type",
            "source_id",
            "source_version",
            "academic_year",
            "subject_code",
            "grade_level",
            "external_item_key",
            "canonical_lesson_id",
            "provenance",
            "status",
            "schema_version",
        }
    )

    _PROVENANCE_KEYS = frozenset(
        {
            "source_document_id",
            "mapping_method",
            "verified_by",
            "source_location",
            "source_version",
        }
    )

    def load_path(
        self,
        path: str | Path,
    ) -> SourceCanonicalBindingDataset:
        source = Path(path)

        try:
            text = source.read_text(
                encoding="utf-8-sig"
            )
        except OSError as error:
            raise SourceCanonicalBindingDataError(
                f"cannot read binding dataset: {source}"
            ) from error

        return self.load_text(text)

    def load_text(
        self,
        text: str,
    ) -> SourceCanonicalBindingDataset:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise SourceCanonicalBindingDataError(
                "binding dataset is not valid JSON"
            ) from error

        return self.load_payload(payload)

    def load_payload(
        self,
        payload: Any,
    ) -> SourceCanonicalBindingDataset:
        if not isinstance(payload, dict):
            raise SourceCanonicalBindingDataError(
                "binding dataset root must be an object"
            )

        self._reject_unknown_keys(
            payload,
            allowed=self._ROOT_KEYS,
            where="dataset root",
        )

        dataset_id = self._required_text(
            payload.get("dataset_id"),
            "dataset_id",
        )

        schema_version = self._positive_int(
            payload.get("schema_version"),
            "schema_version",
        )

        if (
            schema_version
            not in self.SUPPORTED_SCHEMA_VERSIONS
        ):
            raise SourceCanonicalBindingDataError(
                "unsupported binding dataset schema_version: "
                f"{schema_version}"
            )

        raw_bindings = payload.get("bindings")

        if not isinstance(raw_bindings, list):
            raise SourceCanonicalBindingDataError(
                "bindings must be a JSON array"
            )

        bindings = tuple(
            self._parse_binding(
                row,
                index=index,
            )
            for index, row in enumerate(
                raw_bindings,
                start=1,
            )
        )

        self._validate_dataset_uniqueness(
            bindings
        )

        return SourceCanonicalBindingDataset(
            dataset_id=dataset_id,
            schema_version=schema_version,
            bindings=bindings,
        )

    def _parse_binding(
        self,
        payload: Any,
        *,
        index: int,
    ) -> SourceCanonicalBinding:
        if not isinstance(payload, dict):
            raise SourceCanonicalBindingDataError(
                f"bindings[{index}] must be an object"
            )

        self._reject_unknown_keys(
            payload,
            allowed=self._BINDING_KEYS,
            where=f"bindings[{index}]",
        )

        provenance_payload = payload.get(
            "provenance"
        )

        if not isinstance(
            provenance_payload,
            dict,
        ):
            raise SourceCanonicalBindingDataError(
                f"bindings[{index}].provenance "
                "must be an object"
            )

        self._reject_unknown_keys(
            provenance_payload,
            allowed=self._PROVENANCE_KEYS,
            where=(
                f"bindings[{index}].provenance"
            ),
        )

        provenance = (
            SourceCanonicalBindingProvenance(
                source_document_id=self._required_text(
                    provenance_payload.get(
                        "source_document_id"
                    ),
                    (
                        f"bindings[{index}].provenance."
                        "source_document_id"
                    ),
                ),
                mapping_method=self._required_text(
                    provenance_payload.get(
                        "mapping_method"
                    ),
                    (
                        f"bindings[{index}].provenance."
                        "mapping_method"
                    ),
                ),
                verified_by=self._optional_text(
                    provenance_payload.get(
                        "verified_by"
                    )
                ),
                source_location=self._optional_text(
                    provenance_payload.get(
                        "source_location"
                    )
                ),
                source_version=self._optional_text(
                    provenance_payload.get(
                        "source_version"
                    )
                ),
            )
        )

        try:
            return SourceCanonicalBinding(
                binding_id=self._required_text(
                    payload.get("binding_id"),
                    f"bindings[{index}].binding_id",
                ),
                source_type=self._required_text(
                    payload.get("source_type"),
                    f"bindings[{index}].source_type",
                ),
                source_id=self._required_text(
                    payload.get("source_id"),
                    f"bindings[{index}].source_id",
                ),
                source_version=self._required_text(
                    payload.get(
                        "source_version"
                    ),
                    (
                        f"bindings[{index}]."
                        "source_version"
                    ),
                ),
                academic_year=self._required_text(
                    payload.get(
                        "academic_year"
                    ),
                    (
                        f"bindings[{index}]."
                        "academic_year"
                    ),
                ),
                subject_code=self._required_text(
                    payload.get("subject_code"),
                    (
                        f"bindings[{index}]."
                        "subject_code"
                    ),
                ),
                grade_level=self._positive_int(
                    payload.get("grade_level"),
                    (
                        f"bindings[{index}]."
                        "grade_level"
                    ),
                ),
                external_item_key=self._required_text(
                    payload.get(
                        "external_item_key"
                    ),
                    (
                        f"bindings[{index}]."
                        "external_item_key"
                    ),
                ),
                canonical_lesson_id=self._required_text(
                    payload.get(
                        "canonical_lesson_id"
                    ),
                    (
                        f"bindings[{index}]."
                        "canonical_lesson_id"
                    ),
                ),
                provenance=provenance,
                status=self._required_text(
                    payload.get(
                        "status",
                        "CANDIDATE",
                    ),
                    f"bindings[{index}].status",
                ),
                schema_version=self._positive_int(
                    payload.get(
                        "schema_version",
                        1,
                    ),
                    (
                        f"bindings[{index}]."
                        "schema_version"
                    ),
                ),
            )
        except ValueError as error:
            raise SourceCanonicalBindingDataError(
                f"bindings[{index}] is invalid: "
                f"{error}"
            ) from error

    @staticmethod
    def _validate_dataset_uniqueness(
        bindings: tuple[
            SourceCanonicalBinding,
            ...,
        ],
    ) -> None:
        binding_ids: set[str] = set()

        for binding in bindings:
            if binding.binding_id in binding_ids:
                raise SourceCanonicalBindingDataError(
                    "duplicate binding_id in dataset: "
                    f"{binding.binding_id}"
                )
            binding_ids.add(binding.binding_id)

        verified_by_identity: dict[
            object,
            SourceCanonicalBinding,
        ] = {}

        for binding in bindings:
            if binding.status != "VERIFIED":
                continue

            existing = verified_by_identity.get(
                binding.identity
            )

            if existing is not None:
                raise SourceCanonicalBindingDataError(
                    "multiple VERIFIED bindings for "
                    "the same exact source identity: "
                    f"{binding.external_item_key}"
                )

            verified_by_identity[
                binding.identity
            ] = binding

    @staticmethod
    def _reject_unknown_keys(
        payload: dict[str, Any],
        *,
        allowed: frozenset[str],
        where: str,
    ) -> None:
        unknown = sorted(
            set(payload) - set(allowed)
        )

        if unknown:
            raise SourceCanonicalBindingDataError(
                f"{where} contains unknown fields: "
                + ", ".join(unknown)
            )

    @staticmethod
    def _required_text(
        value: Any,
        field: str,
    ) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise SourceCanonicalBindingDataError(
                f"{field} must not be empty"
            )
        return normalized

    @staticmethod
    def _optional_text(
        value: Any,
    ) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def _positive_int(
        value: Any,
        field: str,
    ) -> int:
        if isinstance(value, bool):
            raise SourceCanonicalBindingDataError(
                f"{field} must be a positive integer"
            )

        try:
            normalized = int(value)
        except (TypeError, ValueError) as error:
            raise SourceCanonicalBindingDataError(
                f"{field} must be a positive integer"
            ) from error

        if normalized < 1:
            raise SourceCanonicalBindingDataError(
                f"{field} must be a positive integer"
            )

        return normalized
