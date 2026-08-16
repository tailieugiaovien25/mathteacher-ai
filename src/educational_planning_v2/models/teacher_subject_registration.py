from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TeacherSubjectRegistrationStatus(
    str,
    Enum,
):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@dataclass(frozen=True)
class TeacherSubjectRegistration:
    registration_id: str
    owner_id: str
    academic_year: str
    subject_id: str
    component_id: str | None = None
    status: TeacherSubjectRegistrationStatus = (
        TeacherSubjectRegistrationStatus.ACTIVE
    )

    def __post_init__(self) -> None:
        self._require_text(
            self.registration_id,
            "registration_id",
        )
        self._require_text(
            self.owner_id,
            "owner_id",
        )
        self._require_text(
            self.academic_year,
            "academic_year",
        )
        self._require_text(
            self.subject_id,
            "subject_id",
        )

        if (
            self.component_id is not None
            and not self.component_id.strip()
        ):
            raise ValueError(
                "component_id must be non-empty "
                "when provided"
            )

        if not isinstance(
            self.status,
            TeacherSubjectRegistrationStatus,
        ):
            raise TypeError(
                "status must be "
                "TeacherSubjectRegistrationStatus"
            )

    @staticmethod
    def _require_text(
        value: str,
        field_name: str,
    ) -> None:
        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise ValueError(
                f"{field_name} must be non-empty"
            )

    @property
    def is_subject_level(self) -> bool:
        return self.component_id is None

    @property
    def is_component_level(self) -> bool:
        return self.component_id is not None
