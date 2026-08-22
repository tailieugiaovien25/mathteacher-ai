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

    def build_from_values(
        self,
        *,
        values,
    ) -> LessonPlanModificationPlan:
        """
        Build a modification plan directly from canonical
        document metadata.

        This is the preferred path when authoritative
        metadata already comes from THONG TIN BAI SOAN /
        the weekly teaching schedule.

        Teacher review is intentionally not required here.
        """

        if values is None:
            raise TypeError(
                "values must not be None"
            )

        try:
            items = tuple(
                values.items()
            )
        except AttributeError as error:
            raise TypeError(
                "values must be a mapping"
            ) from error

        modifications = tuple(
            LessonPlanFieldModification(
                field=field,
                value=value,
            )
            for field, value in items
            if value is not None
            and str(value).strip()
        )

        return LessonPlanModificationPlan(
            modifications=modifications
        )
