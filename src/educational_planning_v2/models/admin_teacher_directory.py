from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdminTeacherDirectoryEntry:
    user_id: str
    teacher_code: str
    full_name: str
    school_name: str

    def __post_init__(self) -> None:
        for field_name in (
            "user_id",
            "teacher_code",
            "full_name",
            "school_name",
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
