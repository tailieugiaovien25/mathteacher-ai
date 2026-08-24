from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class TeachingAssignmentRole(str, Enum):
    TEACHING = "TEACHING"
    HOMEROOM = "HOMEROOM"


class TeachingAssignmentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


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
class TeachingAssignment:
    assignment_id: str
    owner_id: str
    academic_year: str
    class_id: str
    role: TeachingAssignmentRole
    effective_from: date
    effective_to: date
    subject_ref: str | None = None
    component_ref: str | None = None
    assignment_round_id: str | None = None
    status: TeachingAssignmentStatus = (
        TeachingAssignmentStatus.ACTIVE
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "assignment_id",
            _required_text(
                self.assignment_id,
                "assignment_id",
                120,
            ),
        )

        object.__setattr__(
            self,
            "owner_id",
            _required_text(
                self.owner_id,
                "owner_id",
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
            "class_id",
            _required_text(
                self.class_id,
                "class_id",
                100,
            ),
        )

        object.__setattr__(
            self,
            "subject_ref",
            _optional_text(
                self.subject_ref,
                "subject_ref",
                100,
            ),
        )

        object.__setattr__(
            self,
            "component_ref",
            _optional_text(
                self.component_ref,
                "component_ref",
                100,
            ),
        )


        object.__setattr__(
            self,
            "assignment_round_id",
            _optional_text(
                self.assignment_round_id,
                "assignment_round_id",
                120,
            ),
        )

        if not isinstance(
            self.role,
            TeachingAssignmentRole,
        ):
            raise TypeError(
                "role must be TeachingAssignmentRole"
            )

        if not isinstance(
            self.status,
            TeachingAssignmentStatus,
        ):
            raise TypeError(
                "status must be TeachingAssignmentStatus"
            )

        if not isinstance(
            self.effective_from,
            date,
        ):
            raise TypeError(
                "effective_from must be a date"
            )

        if not isinstance(
            self.effective_to,
            date,
        ):
            raise TypeError(
                "effective_to must be a date"
            )

        if self.effective_from > self.effective_to:
            raise ValueError(
                "effective_from must not be "
                "after effective_to"
            )

        if (
            self.role
            is TeachingAssignmentRole.TEACHING
            and self.subject_ref is None
        ):
            raise ValueError(
                "TEACHING assignment requires subject_ref"
            )

        if (
            self.role
            is TeachingAssignmentRole.HOMEROOM
            and self.component_ref is not None
        ):
            raise ValueError(
                "HOMEROOM assignment must not "
                "define component_ref"
            )

    @property
    def teaching_key(
        self,
    ) -> tuple[str, str | None, str | None]:
        return (
            self.class_id,
            self.subject_ref,
            self.component_ref,
        )
