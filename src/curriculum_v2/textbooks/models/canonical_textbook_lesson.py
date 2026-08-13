from dataclasses import dataclass


VALID_TEXTBOOK_LESSON_STATUSES = {
    "CANDIDATE",
    "VERIFIED",
    "DEPRECATED",
}


@dataclass(frozen=True)
class TextbookLessonProvenance:
    """Provenance for one canonical textbook lesson record."""

    source_document_id: str
    publisher: str

    verified_copy_id: str | None = None
    source_location: str | None = None
    source_version: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_document_id",
            self._required_text(
                self.source_document_id,
                "source_document_id",
            ),
        )

        object.__setattr__(
            self,
            "publisher",
            self._required_text(
                self.publisher,
                "publisher",
            ),
        )

        for field_name in (
            "verified_copy_id",
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
class CanonicalTextbookLesson:
    """Canonical identity of one lesson/unit in a textbook.

    This contract describes textbook-owned facts only.

    It intentionally does not own:
    - canonical YCCD mappings;
    - curriculum authority;
    - teaching-period allocation;
    - school scheduling;
    - teaching equipment decisions.

    Those responsibilities belong to separate canonical mapping,
    curriculum, and educational-planning layers.
    """

    lesson_id: str
    textbook_ref: str

    subject: str
    grade: int

    title: str
    sequence: int

    provenance: TextbookLessonProvenance

    lesson_kind: str = "LESSON"

    unit_ref: str | None = None
    unit_title: str | None = None

    status: str = "CANDIDATE"
    schema_version: int = 1

    def __post_init__(self) -> None:
        for field_name in (
            "lesson_id",
            "textbook_ref",
            "subject",
            "title",
            "lesson_kind",
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

        if (
            not isinstance(self.grade, int)
            or isinstance(self.grade, bool)
        ):
            raise TypeError(
                "grade must be an int"
            )

        if self.grade <= 0:
            raise ValueError(
                "grade must be greater than 0"
            )

        if (
            not isinstance(self.sequence, int)
            or isinstance(self.sequence, bool)
        ):
            raise TypeError(
                "sequence must be an int"
            )

        if self.sequence <= 0:
            raise ValueError(
                "sequence must be greater than 0"
            )

        if not isinstance(
            self.provenance,
            TextbookLessonProvenance,
        ):
            raise TypeError(
                "provenance must be "
                "TextbookLessonProvenance"
            )

        normalized_status = self.status.upper()

        if (
            normalized_status
            not in VALID_TEXTBOOK_LESSON_STATUSES
        ):
            raise ValueError(
                "status must be one of: "
                "CANDIDATE, VERIFIED, DEPRECATED"
            )

        object.__setattr__(
            self,
            "status",
            normalized_status,
        )

        normalized_kind = (
            self.lesson_kind
            .strip()
            .upper()
        )

        object.__setattr__(
            self,
            "lesson_kind",
            normalized_kind,
        )

        for field_name in (
            "unit_ref",
            "unit_title",
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
