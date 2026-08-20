from __future__ import annotations

from dataclasses import dataclass

from document_intelligence.contracts import (
    DocumentField,
)
from document_intelligence.lesson_plan_teacher_review_resolver import (
    LessonPlanTeacherReviewResolution,
)


@dataclass(frozen=True)
class LessonPlanFieldModification:
    field: DocumentField
    value: str

    def __post_init__(self) -> None:
        if not isinstance(
            self.field,
            DocumentField,
        ):
            raise TypeError(
                "field must be DocumentField"
            )

        normalized = str(
            self.value
        ).strip()

        if not normalized:
            raise ValueError(
                "modification value must not be empty"
            )

        object.__setattr__(
            self,
            "value",
            normalized,
        )


@dataclass(frozen=True)
class LessonPlanModificationPlan:
    modifications: tuple[
        LessonPlanFieldModification,
        ...
    ] = ()

    def value_for(
        self,
        field: DocumentField,
    ) -> str | None:
        for modification in self.modifications:
            if modification.field is field:
                return modification.value

        return None

    @property
    def is_empty(self) -> bool:
        return not self.modifications


class LessonPlanModificationPlanner:
    def build(
        self,
        *,
        resolution: LessonPlanTeacherReviewResolution,
    ) -> LessonPlanModificationPlan:
        if not isinstance(
            resolution,
            LessonPlanTeacherReviewResolution,
        ):
            raise TypeError(
                "resolution must be "
                "LessonPlanTeacherReviewResolution"
            )

        if not resolution.accepted:
            raise ValueError(
                "teacher review must be accepted "
                "before building modification plan"
            )

        modifications = tuple(
            LessonPlanFieldModification(
                field=field,
                value=value,
            )
            for field, value
            in resolution.metadata.values
        )

        return LessonPlanModificationPlan(
            modifications=modifications
        )
