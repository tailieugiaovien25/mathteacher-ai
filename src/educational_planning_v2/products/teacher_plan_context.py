from dataclasses import dataclass


@dataclass(frozen=True)
class TeacherPlanContext:
    """Administrative context for a teacher educational-plan product."""

    school_name: str
    professional_team: str
    teacher_name: str
    academic_year: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "school_name",
            self._require_text(self.school_name, "school_name"),
        )
        object.__setattr__(
            self,
            "professional_team",
            self._require_text(self.professional_team, "professional_team"),
        )
        object.__setattr__(
            self,
            "teacher_name",
            self._require_text(self.teacher_name, "teacher_name"),
        )
        object.__setattr__(
            self,
            "academic_year",
            self._require_text(self.academic_year, "academic_year"),
        )

    @staticmethod
    def _require_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")

        normalized = value.strip()

        if not normalized:
            raise ValueError(f"{field_name} must not be empty")

        return normalized