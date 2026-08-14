"""Teacher-owned profile used by planning and document products."""

from __future__ import annotations

from dataclasses import dataclass


def _required_text(value: str, field_name: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(normalized) > maximum:
        raise ValueError(f"{field_name} must not exceed {maximum} characters")
    return normalized


def _text_tuple(value: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    normalized = tuple(
        _required_text(item, f"{field_name} item", 100) for item in value
    )
    return tuple(dict.fromkeys(normalized))


@dataclass(frozen=True)
class TeacherProfile:
    teacher_code: str
    full_name: str
    school_name: str
    subjects: tuple[str, ...]
    grade_levels: tuple[str, ...]
    default_academic_year: str
    show_teacher_name: bool = True
    show_school_name: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "teacher_code", _required_text(self.teacher_code, "teacher_code", 100))
        object.__setattr__(self, "full_name", _required_text(self.full_name, "full_name", 200))
        object.__setattr__(self, "school_name", _required_text(self.school_name, "school_name", 250))
        object.__setattr__(self, "subjects", _text_tuple(self.subjects, "subjects"))
        object.__setattr__(self, "grade_levels", _text_tuple(self.grade_levels, "grade_levels"))
        object.__setattr__(self, "default_academic_year", _required_text(self.default_academic_year, "default_academic_year", 30))
        if not self.subjects:
            raise ValueError("subjects must not be empty")
        if not self.grade_levels:
            raise ValueError("grade_levels must not be empty")
        if not isinstance(self.show_teacher_name, bool):
            raise TypeError("show_teacher_name must be a bool")
        if not isinstance(self.show_school_name, bool):
            raise TypeError("show_school_name must be a bool")
