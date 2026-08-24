from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LessonPlanTeachingScopeType(str, Enum):
    CLASS = "class"
    GRADE = "grade"


@dataclass(frozen=True)
class LessonPlanTeachingScope:
    scope_type: LessonPlanTeachingScopeType
    scope_ref: str

    def __post_init__(self) -> None:
        normalized_ref = str(
            self.scope_ref or ""
        ).strip()

        if not normalized_ref:
            raise ValueError(
                "scope_ref must not be blank"
            )

        object.__setattr__(
            self,
            "scope_ref",
            normalized_ref,
        )

    @classmethod
    def for_class(
        cls,
        *,
        class_id: str,
    ) -> "LessonPlanTeachingScope":
        normalized = str(
            class_id or ""
        ).strip()

        if not normalized:
            raise ValueError(
                "class_id must not be blank"
            )

        return cls(
            scope_type=(
                LessonPlanTeachingScopeType.CLASS
            ),
            scope_ref=normalized,
        )

    @classmethod
    def for_grade(
        cls,
        *,
        grade_key: str,
    ) -> "LessonPlanTeachingScope":
        normalized = str(
            grade_key or ""
        ).strip()

        if not normalized:
            raise ValueError(
                "grade_key must not be blank"
            )

        return cls(
            scope_type=(
                LessonPlanTeachingScopeType.GRADE
            ),
            scope_ref=normalized,
        )

    @property
    def class_id(self) -> str | None:
        if (
            self.scope_type
            is LessonPlanTeachingScopeType.CLASS
        ):
            return self.scope_ref

        return None

    @property
    def grade_key(self) -> str | None:
        if (
            self.scope_type
            is LessonPlanTeachingScopeType.GRADE
        ):
            return self.scope_ref

        return None

    @property
    def identity_key(
        self,
    ) -> tuple[str, str]:
        return (
            self.scope_type.value,
            self.scope_ref,
        )
