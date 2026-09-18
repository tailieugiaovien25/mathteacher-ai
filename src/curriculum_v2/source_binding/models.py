"""Generic source-to-canonical binding models.

These contracts deliberately keep operational source data outside the
canonical curriculum domain. A source adapter may represent PPCT, Excel,
Drive, an API, or a future provider, but every adapter must emit the same
CurriculumSourceItem identity contract.

Runtime resolution is exact. Titles are display metadata only and are never
used as a fallback key for canonical mapping.
"""

from __future__ import annotations

from dataclasses import dataclass


class SourceCanonicalBindingValidationError(ValueError):
    """Raised when source/binding data violates the stable contract."""


def _required_text(value: object, field: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise SourceCanonicalBindingValidationError(
            f"{field} must not be empty"
        )
    return normalized


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _grade(value: object) -> int:
    if isinstance(value, bool):
        raise SourceCanonicalBindingValidationError(
            "grade_level must be an integer from 1 to 12"
        )

    try:
        normalized = int(value)
    except (TypeError, ValueError) as error:
        raise SourceCanonicalBindingValidationError(
            "grade_level must be an integer from 1 to 12"
        ) from error

    if normalized < 1 or normalized > 12:
        raise SourceCanonicalBindingValidationError(
            "grade_level must be an integer from 1 to 12"
        )

    return normalized


@dataclass(frozen=True, slots=True)
class SourceItemIdentity:
    """Exact identity emitted by a source adapter."""

    source_type: str
    source_id: str
    source_version: str
    academic_year: str
    subject_code: str
    grade_level: int
    external_item_key: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_type",
            _required_text(
                self.source_type,
                "source_type",
            ).upper(),
        )
        object.__setattr__(
            self,
            "source_id",
            _required_text(
                self.source_id,
                "source_id",
            ),
        )
        object.__setattr__(
            self,
            "source_version",
            _required_text(
                self.source_version,
                "source_version",
            ),
        )
        object.__setattr__(
            self,
            "academic_year",
            _required_text(
                self.academic_year,
                "academic_year",
            ),
        )
        object.__setattr__(
            self,
            "subject_code",
            _required_text(
                self.subject_code,
                "subject_code",
            ).upper(),
        )
        object.__setattr__(
            self,
            "grade_level",
            _grade(self.grade_level),
        )
        object.__setattr__(
            self,
            "external_item_key",
            _required_text(
                self.external_item_key,
                "external_item_key",
            ),
        )


@dataclass(frozen=True, slots=True)
class CurriculumSourceItem:
    """Source-neutral operational curriculum item.

    ``title`` and ``sequence`` are evidence/display fields only. They are not
    part of canonical resolution and must never be used as fuzzy fallbacks.
    """

    source_type: str
    source_id: str
    source_version: str
    academic_year: str
    subject_code: str
    grade_level: int
    external_item_key: str
    sequence: int | None = None
    title: str | None = None
    source_location: str | None = None

    def __post_init__(self) -> None:
        identity = SourceItemIdentity(
            source_type=self.source_type,
            source_id=self.source_id,
            source_version=self.source_version,
            academic_year=self.academic_year,
            subject_code=self.subject_code,
            grade_level=self.grade_level,
            external_item_key=self.external_item_key,
        )

        object.__setattr__(
            self,
            "source_type",
            identity.source_type,
        )
        object.__setattr__(
            self,
            "source_id",
            identity.source_id,
        )
        object.__setattr__(
            self,
            "source_version",
            identity.source_version,
        )
        object.__setattr__(
            self,
            "academic_year",
            identity.academic_year,
        )
        object.__setattr__(
            self,
            "subject_code",
            identity.subject_code,
        )
        object.__setattr__(
            self,
            "grade_level",
            identity.grade_level,
        )
        object.__setattr__(
            self,
            "external_item_key",
            identity.external_item_key,
        )

        if self.sequence is not None:
            if isinstance(self.sequence, bool):
                raise SourceCanonicalBindingValidationError(
                    "sequence must be a positive integer or None"
                )
            try:
                sequence = int(self.sequence)
            except (TypeError, ValueError) as error:
                raise SourceCanonicalBindingValidationError(
                    "sequence must be a positive integer or None"
                ) from error
            if sequence < 1:
                raise SourceCanonicalBindingValidationError(
                    "sequence must be a positive integer or None"
                )
            object.__setattr__(
                self,
                "sequence",
                sequence,
            )

        object.__setattr__(
            self,
            "title",
            _optional_text(self.title),
        )
        object.__setattr__(
            self,
            "source_location",
            _optional_text(
                self.source_location
            ),
        )

    @property
    def identity(self) -> SourceItemIdentity:
        return SourceItemIdentity(
            source_type=self.source_type,
            source_id=self.source_id,
            source_version=self.source_version,
            academic_year=self.academic_year,
            subject_code=self.subject_code,
            grade_level=self.grade_level,
            external_item_key=self.external_item_key,
        )


@dataclass(frozen=True, slots=True)
class SourceCanonicalBindingProvenance:
    """Audit evidence for a source-to-canonical decision."""

    source_document_id: str
    mapping_method: str
    verified_by: str | None = None
    source_location: str | None = None
    source_version: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_document_id",
            _required_text(
                self.source_document_id,
                "source_document_id",
            ),
        )
        object.__setattr__(
            self,
            "mapping_method",
            _required_text(
                self.mapping_method,
                "mapping_method",
            ).upper(),
        )
        object.__setattr__(
            self,
            "verified_by",
            _optional_text(self.verified_by),
        )
        object.__setattr__(
            self,
            "source_location",
            _optional_text(
                self.source_location
            ),
        )
        object.__setattr__(
            self,
            "source_version",
            _optional_text(
                self.source_version
            ),
        )


@dataclass(frozen=True, slots=True)
class SourceCanonicalBinding:
    """Versioned data binding from one exact source item to one lesson."""

    binding_id: str
    source_type: str
    source_id: str
    source_version: str
    academic_year: str
    subject_code: str
    grade_level: int
    external_item_key: str
    canonical_lesson_id: str
    provenance: SourceCanonicalBindingProvenance
    status: str = "CANDIDATE"
    schema_version: int = 1

    _ALLOWED_STATUSES = frozenset(
        {
            "CANDIDATE",
            "VERIFIED",
            "DEPRECATED",
        }
    )

    def __post_init__(self) -> None:
        identity = SourceItemIdentity(
            source_type=self.source_type,
            source_id=self.source_id,
            source_version=self.source_version,
            academic_year=self.academic_year,
            subject_code=self.subject_code,
            grade_level=self.grade_level,
            external_item_key=self.external_item_key,
        )

        object.__setattr__(
            self,
            "binding_id",
            _required_text(
                self.binding_id,
                "binding_id",
            ),
        )
        object.__setattr__(
            self,
            "source_type",
            identity.source_type,
        )
        object.__setattr__(
            self,
            "source_id",
            identity.source_id,
        )
        object.__setattr__(
            self,
            "source_version",
            identity.source_version,
        )
        object.__setattr__(
            self,
            "academic_year",
            identity.academic_year,
        )
        object.__setattr__(
            self,
            "subject_code",
            identity.subject_code,
        )
        object.__setattr__(
            self,
            "grade_level",
            identity.grade_level,
        )
        object.__setattr__(
            self,
            "external_item_key",
            identity.external_item_key,
        )
        object.__setattr__(
            self,
            "canonical_lesson_id",
            _required_text(
                self.canonical_lesson_id,
                "canonical_lesson_id",
            ),
        )

        if not isinstance(
            self.provenance,
            SourceCanonicalBindingProvenance,
        ):
            raise SourceCanonicalBindingValidationError(
                "provenance must be "
                "SourceCanonicalBindingProvenance"
            )

        status = _required_text(
            self.status,
            "status",
        ).upper()

        if status not in self._ALLOWED_STATUSES:
            raise SourceCanonicalBindingValidationError(
                "status must be one of "
                "CANDIDATE, VERIFIED, DEPRECATED"
            )

        object.__setattr__(
            self,
            "status",
            status,
        )

        if isinstance(self.schema_version, bool):
            raise SourceCanonicalBindingValidationError(
                "schema_version must be a positive integer"
            )

        try:
            schema_version = int(
                self.schema_version
            )
        except (TypeError, ValueError) as error:
            raise SourceCanonicalBindingValidationError(
                "schema_version must be a positive integer"
            ) from error

        if schema_version < 1:
            raise SourceCanonicalBindingValidationError(
                "schema_version must be a positive integer"
            )

        object.__setattr__(
            self,
            "schema_version",
            schema_version,
        )

    @property
    def identity(self) -> SourceItemIdentity:
        return SourceItemIdentity(
            source_type=self.source_type,
            source_id=self.source_id,
            source_version=self.source_version,
            academic_year=self.academic_year,
            subject_code=self.subject_code,
            grade_level=self.grade_level,
            external_item_key=self.external_item_key,
        )
