from dataclasses import dataclass


VALID_MAPPING_STATUSES = {
    "CANDIDATE",
    "VERIFIED",
    "DEPRECATED",
}


@dataclass(frozen=True)
class TextbookRequirementMappingProvenance:
    """Provenance for one textbook-to-canonical-requirement mapping."""

    source_document_id: str
    mapping_method: str

    verified_by: str | None = None
    source_location: str | None = None
    source_version: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "source_document_id",
            "mapping_method",
        ):
            object.__setattr__(
                self,
                field_name,
                self._required_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        for field_name in (
            "verified_by",
            "source_location",
            "source_version",
        ):
            value = getattr(self, field_name)

            if value is None:
                continue

            object.__setattr__(
                self,
                field_name,
                self._required_text(
                    value,
                    field_name,
                ),
            )

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized


@dataclass(frozen=True)
class TextbookRequirementMapping:
    """Canonical mapping between one textbook lesson and one YCCD."""

    mapping_id: str

    lesson_id: str
    canonical_requirement_id: str

    provenance: TextbookRequirementMappingProvenance

    status: str = "CANDIDATE"
    schema_version: int = 1

    def __post_init__(self) -> None:
        for field_name in (
            "mapping_id",
            "lesson_id",
            "canonical_requirement_id",
            "status",
        ):
            object.__setattr__(
                self,
                field_name,
                self._required_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if not isinstance(
            self.provenance,
            TextbookRequirementMappingProvenance,
        ):
            raise TypeError(
                "provenance must be "
                "TextbookRequirementMappingProvenance"
            )

        normalized_status = self.status.upper()

        if normalized_status not in VALID_MAPPING_STATUSES:
            raise ValueError(
                "status must be one of: "
                "CANDIDATE, VERIFIED, DEPRECATED"
            )

        object.__setattr__(
            self,
            "status",
            normalized_status,
        )

        if (
            not isinstance(self.schema_version, int)
            or isinstance(self.schema_version, bool)
        ):
            raise TypeError(
                "schema_version must be an int"
            )

        if self.schema_version <= 0:
            raise ValueError(
                "schema_version must be greater than 0"
            )

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized
