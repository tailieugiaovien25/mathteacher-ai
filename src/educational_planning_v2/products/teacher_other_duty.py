from dataclasses import dataclass


@dataclass(frozen=True)
class TeacherOtherDuty:
    """One additional duty in a teacher educational-plan product."""

    duty_id: str
    title: str
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "duty_id",
            self._require_text(self.duty_id, "duty_id"),
        )
        object.__setattr__(
            self,
            "title",
            self._require_text(self.title, "title"),
        )
        object.__setattr__(
            self,
            "description",
            self._normalize_optional_text(self.description),
        )

    @staticmethod
    def _require_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")

        normalized = value.strip()

        if not normalized:
            raise ValueError(f"{field_name} must not be empty")

        return normalized

    @staticmethod
    def _normalize_optional_text(value: str) -> str:
        if not isinstance(value, str):
            raise TypeError("description must be a string")

        return value.strip()