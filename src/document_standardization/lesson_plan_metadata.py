from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import date
from typing import Any


@dataclass(frozen=True, slots=True)
class LessonPlanMetadata:
    """
    Canonical metadata used when overlaying information
    onto an existing lesson-plan DOCX.

    None means:
        do not modify the corresponding value
        in the source document.

    Empty strings are normalized to None.
    """

    school_name: str | None = None
    teacher_name: str | None = None
    subject_name: str | None = None
    class_name: str | None = None
    lesson_title: str | None = None
    curriculum_period: int | None = None
    drafting_date: date | None = None
    teaching_date: date | None = None

    def __post_init__(self) -> None:
        string_fields = (
            "school_name",
            "teacher_name",
            "subject_name",
            "class_name",
            "lesson_title",
        )

        for name in string_fields:
            value = getattr(
                self,
                name,
            )

            if value is None:
                continue

            if not isinstance(
                value,
                str,
            ):
                raise TypeError(
                    f"{name} must be str or None"
                )

            normalized = value.strip()

            object.__setattr__(
                self,
                name,
                normalized or None,
            )

        if self.curriculum_period is not None:
            value = self.curriculum_period

            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value <= 0
            ):
                raise ValueError(
                    "curriculum_period must be "
                    "a positive integer or None"
                )

        for name in (
            "drafting_date",
            "teaching_date",
        ):
            value = getattr(
                self,
                name,
            )

            if (
                value is not None
                and not isinstance(
                    value,
                    date,
                )
            ):
                raise TypeError(
                    f"{name} must be date or None"
                )

    @property
    def is_empty(self) -> bool:
        return all(
            getattr(
                self,
                field.name,
            )
            is None
            for field in fields(self)
        )

    def overlay_values(
        self,
    ) -> dict[str, Any]:
        """
        Return only metadata explicitly supplied
        by the caller.

        Missing values are intentionally excluded
        so the overlay engine cannot accidentally
        erase existing document metadata.
        """

        return {
            field.name: getattr(
                self,
                field.name,
            )
            for field in fields(self)
            if getattr(
                self,
                field.name,
            )
            is not None
        }

    def display_values(
        self,
    ) -> dict[str, str]:
        """
        Human-readable representation suitable
        for preview/reporting.
        """

        result: dict[str, str] = {}

        for name, value in (
            self.overlay_values()
            .items()
        ):
            if isinstance(
                value,
                date,
            ):
                result[name] = (
                    value.strftime(
                        "%d/%m/%Y"
                    )
                )
            else:
                result[name] = str(
                    value
                )

        return result
