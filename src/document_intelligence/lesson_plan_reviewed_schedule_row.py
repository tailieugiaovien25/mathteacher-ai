from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping

from document_intelligence.contracts import DocumentField
from educational_planning_v2.models.teacher_timetable import TeachingSession


@dataclass(frozen=True)
class LessonPlanReviewedScheduleRow:
    """
    Immutable processing adapter.

    Keeps weekly-schedule identity/technical metadata while applying
    teacher-approved document metadata at the document-processing
    boundary.

    The original weekly schedule row is never mutated.
    """

    teaching_date: date
    weekday: int
    timetable_period: int
    session: Any

    class_id: str
    subject_ref: str
    component_ref: str | None

    curriculum_period: int

    lesson_id: str
    lesson_title: str
    period_in_lesson: int

    teaching_equipment: tuple[Any, ...]

    @classmethod
    def from_schedule_row(
        cls,
        *,
        row: Any,
        resolved_metadata: Mapping[
            DocumentField,
            str | None,
        ],
    ) -> "LessonPlanReviewedScheduleRow":
        def resolved_text(
            field: DocumentField,
            fallback: str,
        ) -> str:
            value = resolved_metadata.get(field)

            if value is None:
                return fallback

            normalized = str(value).strip()

            if not normalized:
                return fallback

            return normalized

        class_id = resolved_text(
            DocumentField.CLASS_NAME,
            row.class_id,
        )

        lesson_title = resolved_text(
            DocumentField.LESSON_TITLE,
            row.lesson_title,
        )

        curriculum_period_text = resolved_text(
            DocumentField.CURRICULUM_PERIOD,
            str(row.curriculum_period),
        )

        try:
            curriculum_period = int(
                curriculum_period_text
            )
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Resolved curriculum period "
                "must be an integer."
            ) from error

        teaching_date = row.teaching_date

        teaching_date_text = resolved_metadata.get(
            DocumentField.TEACHING_DATE
        )

        if teaching_date_text:
            try:
                teaching_date = date.fromisoformat(
                    str(teaching_date_text)
                    .strip()
                )
            except ValueError:
                try:
                    teaching_date = (
                        date(
                            int(
                                str(
                                    teaching_date_text
                                )
                                .strip()
                                .split("/")[2]
                            ),
                            int(
                                str(
                                    teaching_date_text
                                )
                                .strip()
                                .split("/")[1]
                            ),
                            int(
                                str(
                                    teaching_date_text
                                )
                                .strip()
                                .split("/")[0]
                            ),
                        )
                    )
                except (
                    IndexError,
                    TypeError,
                    ValueError,
                ) as error:
                    raise ValueError(
                        "Resolved teaching date "
                        "must use ISO or DD/MM/YYYY."
                    ) from error

        return cls(
            teaching_date=teaching_date,
            weekday=row.weekday,
            timetable_period=(
                row.timetable_period
            ),
            session=(
                row.session
                if isinstance(
                    row.session,
                    TeachingSession,
                )
                else TeachingSession(
                    (
                        str(row.session)
                        .strip()
                        .removeprefix(
                            "TeachingSession."
                        )
                    )
                )
            ),
            class_id=class_id,
            subject_ref=row.subject_ref,
            component_ref=row.component_ref,
            curriculum_period=(
                curriculum_period
            ),
            lesson_id=row.lesson_id,
            lesson_title=lesson_title,
            period_in_lesson=(
                row.period_in_lesson
            ),
            teaching_equipment=tuple(
                row.teaching_equipment
            ),
        )
