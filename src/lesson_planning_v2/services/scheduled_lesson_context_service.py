from datetime import date

from lesson_planning_v2.contexts import (
    ScheduledLessonContext,
)


class ScheduledLessonContextService:
    """
    Build a concrete teaching context from a weekly
    schedule portal row.

    This service owns no Streamlit, storage, Word, or
    curriculum-resolution responsibility.
    """

    def build_from_weekly_schedule_row(
        self,
        row,
        *,
        drafting_date: date | None = None,
    ) -> ScheduledLessonContext:
        required_attributes = (
            "teaching_date",
            "class_id",
            "subject_ref",
            "component_ref",
            "curriculum_period",
            "lesson_id",
            "lesson_title",
            "session",
            "timetable_period",
            "period_in_lesson",
        )

        for name in required_attributes:
            if not hasattr(
                row,
                name,
            ):
                raise TypeError(
                    "weekly schedule row is missing "
                    f"required attribute: {name}"
                )

        return ScheduledLessonContext(
            teaching_date=row.teaching_date,
            drafting_date=drafting_date,
            class_id=row.class_id,
            subject_ref=row.subject_ref,
            component_ref=row.component_ref,
            curriculum_period=row.curriculum_period,
            lesson_id=row.lesson_id,
            lesson_title=row.lesson_title,
            session=row.session,
            timetable_period=row.timetable_period,
            period_in_lesson=row.period_in_lesson,
        )


def get_scheduled_lesson_context_service(
) -> ScheduledLessonContextService:
    return ScheduledLessonContextService()
