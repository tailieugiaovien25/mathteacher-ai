from dataclasses import dataclass
from datetime import date

from educational_planning_v2.models import (
    TeachingSession,
)


@dataclass(frozen=True)
class ScheduledLessonContext:
    """
    Context of one concrete teaching occurrence.

    This model deliberately owns scheduling metadata,
    not curriculum-resolution responsibility.
    """

    teaching_date: date
    drafting_date: date | None

    class_id: str

    subject_ref: str
    component_ref: str | None

    curriculum_period: int

    lesson_id: str
    lesson_title: str

    session: TeachingSession
    timetable_period: int
    period_in_lesson: int

    def __post_init__(self) -> None:
        if not isinstance(
            self.teaching_date,
            date,
        ):
            raise TypeError(
                "teaching_date must be date"
            )

        if (
            self.drafting_date is not None
            and not isinstance(
                self.drafting_date,
                date,
            )
        ):
            raise TypeError(
                "drafting_date must be date or None"
            )

        if (
            self.drafting_date is not None
            and self.drafting_date
            > self.teaching_date
        ):
            raise ValueError(
                "drafting_date must not be after teaching_date"
            )

        for name in (
            "curriculum_period",
            "timetable_period",
            "period_in_lesson",
        ):
            value = getattr(
                self,
                name,
            )

            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value <= 0
            ):
                raise ValueError(
                    f"{name} must be a positive integer"
                )

        for name in (
            "class_id",
            "subject_ref",
            "lesson_id",
            "lesson_title",
        ):
            value = getattr(
                self,
                name,
            )

            if not isinstance(
                value,
                str,
            ):
                raise TypeError(
                    f"{name} must be str"
                )

            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"{name} must not be empty"
                )

            object.__setattr__(
                self,
                name,
                normalized,
            )

        if self.component_ref is not None:
            if not isinstance(
                self.component_ref,
                str,
            ):
                raise TypeError(
                    "component_ref must be str or None"
                )

            normalized_component = (
                self.component_ref.strip()
            )

            object.__setattr__(
                self,
                "component_ref",
                normalized_component or None,
            )

        if not isinstance(
            self.session,
            TeachingSession,
        ):
            raise TypeError(
                "session must be TeachingSession"
            )
