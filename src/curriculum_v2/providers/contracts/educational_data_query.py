from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EducationalDataQuery:
    """Provider-neutral educational data query."""

    capability: str

    curriculum_ref: str | None = None
    textbook_ref: str | None = None
    subject_ref: str | None = None
    grade_ref: str | None = None

    version_ref: str | None = None

    filters: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "capability",
            self._required_text(
                self.capability,
                "capability",
            ),
        )

        for field_name in (
            "curriculum_ref",
            "textbook_ref",
            "subject_ref",
            "grade_ref",
            "version_ref",
        ):
            value = getattr(
                self,
                field_name,
            )

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

        if not isinstance(
            self.filters,
            tuple,
        ):
            raise TypeError(
                "filters must be a tuple"
            )

        normalized_filters = []

        for item in self.filters:
            if (
                not isinstance(item, tuple)
                or len(item) != 2
            ):
                raise TypeError(
                    "each filter must be a "
                    "(key, value) tuple"
                )

            key, value = item

            key = self._required_text(
                key,
                "filter key",
            )

            normalized_filters.append(
                (key, value)
            )

        object.__setattr__(
            self,
            "filters",
            tuple(normalized_filters),
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
