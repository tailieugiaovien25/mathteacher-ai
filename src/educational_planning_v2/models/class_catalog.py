from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ClassCatalogStatus(
    str,
    Enum,
):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


def _required_text(
    value: str,
    field_name: str,
    maximum: int = 250,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise TypeError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{field_name} must not be empty"
        )

    if len(normalized) > maximum:
        raise ValueError(
            f"{field_name} must not exceed "
            f"{maximum} characters"
        )

    return normalized


@dataclass(frozen=True)
class ClassCatalog:
    class_id: str
    academic_year: str
    grade_level: str
    class_code: str
    class_name: str
    status: ClassCatalogStatus = (
        ClassCatalogStatus.ACTIVE
    )

    def __post_init__(
        self,
    ) -> None:
        object.__setattr__(
            self,
            "class_id",
            _required_text(
                self.class_id,
                "class_id",
                120,
            ),
        )

        object.__setattr__(
            self,
            "academic_year",
            _required_text(
                self.academic_year,
                "academic_year",
                30,
            ),
        )

        object.__setattr__(
            self,
            "grade_level",
            _required_text(
                self.grade_level,
                "grade_level",
                50,
            ),
        )

        object.__setattr__(
            self,
            "class_code",
            _required_text(
                self.class_code,
                "class_code",
                100,
            ),
        )

        object.__setattr__(
            self,
            "class_name",
            _required_text(
                self.class_name,
                "class_name",
                200,
            ),
        )

        if not isinstance(
            self.status,
            ClassCatalogStatus,
        ):
            raise TypeError(
                "status must be ClassCatalogStatus"
            )

    @property
    def display_name(
        self,
    ) -> str:
        return self.class_name
