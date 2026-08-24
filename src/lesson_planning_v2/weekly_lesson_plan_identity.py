from __future__ import annotations

from dataclasses import dataclass

from lesson_planning_v2.lesson_plan_teaching_scope import (
    LessonPlanTeachingScope,
)


@dataclass(frozen=True)
class WeeklyLessonPlanIdentity:
    teacher_id: str
    academic_year: str
    week_number: int
    subject_ref: str
    teaching_scope: LessonPlanTeachingScope

    def __post_init__(self) -> None:
        teacher_id = str(
            self.teacher_id or ""
        ).strip()

        academic_year = str(
            self.academic_year or ""
        ).strip()

        subject_ref = str(
            self.subject_ref or ""
        ).strip()

        if not teacher_id:
            raise ValueError(
                "teacher_id must not be blank"
            )

        if not academic_year:
            raise ValueError(
                "academic_year must not be blank"
            )

        if not subject_ref:
            raise ValueError(
                "subject_ref must not be blank"
            )

        if (
            not isinstance(
                self.week_number,
                int,
            )
            or isinstance(
                self.week_number,
                bool,
            )
            or self.week_number <= 0
        ):
            raise ValueError(
                "week_number must be positive"
            )

        if not isinstance(
            self.teaching_scope,
            LessonPlanTeachingScope,
        ):
            raise TypeError(
                "teaching_scope must be "
                "LessonPlanTeachingScope"
            )

        object.__setattr__(
            self,
            "teacher_id",
            teacher_id,
        )

        object.__setattr__(
            self,
            "academic_year",
            academic_year,
        )

        object.__setattr__(
            self,
            "subject_ref",
            subject_ref,
        )

    @property
    def identity_key(
        self,
    ) -> tuple[
        str,
        str,
        int,
        str,
        str,
        str,
    ]:
        scope_type, scope_ref = (
            self.teaching_scope.identity_key
        )

        return (
            self.teacher_id,
            self.academic_year,
            self.week_number,
            self.subject_ref,
            scope_type,
            scope_ref,
        )
