from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TeacherSubjectAssignmentStatus(
    str,
    Enum,
):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@dataclass(frozen=True)
class TeacherSubjectAssignment:
    assignment_id: str
    teacher_id: str
    academic_year: str
    subject_id: str
    status: TeacherSubjectAssignmentStatus = (
        TeacherSubjectAssignmentStatus.ACTIVE
    )

    def __post_init__(self) -> None:
        for field_name in (
            "assignment_id",
            "teacher_id",
            "academic_year",
            "subject_id",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                str,
            ):
                raise TypeError(
                    f"{field_name} must be str"
                )

            normalized = (
                value.strip()
            )

            if not normalized:
                raise ValueError(
                    f"{field_name} must not be empty"
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )

        if not isinstance(
            self.status,
            TeacherSubjectAssignmentStatus,
        ):
            raise TypeError(
                "status must be "
                "TeacherSubjectAssignmentStatus"
            )

    @property
    def assignment_key(
        self,
    ) -> tuple[str, str, str]:
        return (
            self.teacher_id,
            self.academic_year,
            self.subject_id,
        )
