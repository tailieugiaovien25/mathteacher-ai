from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CatalogStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class SubjectComponentPolicy(str, Enum):
    NONE = "NONE"
    OPTIONAL = "OPTIONAL"
    REQUIRED = "REQUIRED"


def _required_text(
    value: str,
    field_name: str,
    maximum: int = 250,
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

    if len(normalized) > maximum:
        raise ValueError(
            f"{field_name} must not exceed "
            f"{maximum} characters"
        )

    return normalized


def _optional_text(
    value: str | None,
    field_name: str,
    maximum: int = 250,
) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string or None"
        )

    normalized = value.strip()

    if not normalized:
        return None

    if len(normalized) > maximum:
        raise ValueError(
            f"{field_name} must not exceed "
            f"{maximum} characters"
        )

    return normalized


@dataclass(frozen=True)
class Subject:
    subject_id: str
    code: str
    name: str
    component_policy: SubjectComponentPolicy
    status: CatalogStatus = CatalogStatus.ACTIVE
    display_order: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "subject_id",
            _required_text(
                self.subject_id,
                "subject_id",
                120,
            ),
        )

        object.__setattr__(
            self,
            "code",
            _required_text(
                self.code,
                "code",
                100,
            ),
        )

        object.__setattr__(
            self,
            "name",
            _required_text(
                self.name,
                "name",
                200,
            ),
        )

        if not isinstance(
            self.component_policy,
            SubjectComponentPolicy,
        ):
            raise TypeError(
                "component_policy must be "
                "SubjectComponentPolicy"
            )

        if not isinstance(
            self.status,
            CatalogStatus,
        ):
            raise TypeError(
                "status must be CatalogStatus"
            )

        if (
            not isinstance(
                self.display_order,
                int,
            )
            or isinstance(
                self.display_order,
                bool,
            )
        ):
            raise TypeError(
                "display_order must be an int"
            )

        if self.display_order < 0:
            raise ValueError(
                "display_order must not be negative"
            )


@dataclass(frozen=True)
class SubjectComponent:
    component_id: str
    subject_id: str
    code: str
    name: str
    status: CatalogStatus = CatalogStatus.ACTIVE
    display_order: int = 0
    description: str | None = None

    def __post_init__(self) -> None:
        for field_name, maximum in (
            ("component_id", 120),
            ("subject_id", 120),
            ("code", 100),
            ("name", 200),
        ):
            object.__setattr__(
                self,
                field_name,
                _required_text(
                    getattr(
                        self,
                        field_name,
                    ),
                    field_name,
                    maximum,
                ),
            )

        if not isinstance(
            self.status,
            CatalogStatus,
        ):
            raise TypeError(
                "status must be CatalogStatus"
            )

        if (
            not isinstance(
                self.display_order,
                int,
            )
            or isinstance(
                self.display_order,
                bool,
            )
        ):
            raise TypeError(
                "display_order must be an int"
            )

        if self.display_order < 0:
            raise ValueError(
                "display_order must not be negative"
            )

        object.__setattr__(
            self,
            "description",
            _optional_text(
                self.description,
                "description",
                500,
            ),
        )
