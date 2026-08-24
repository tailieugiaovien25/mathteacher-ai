from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from educational_planning_v2.models import (
    TeachingSession,
)
from lesson_planning_v2.contexts import (
    ScheduledLessonContext,
)


def make_context(
    *,
    drafting_date=date(2026, 9, 27),
):
    return ScheduledLessonContext(
        teaching_date=date(2026, 9, 28),
        drafting_date=drafting_date,
        class_id=" 6A1 ",
        subject_ref=" MATHEMATICS ",
        component_ref=" ALGEBRA ",
        curriculum_period=9,
        lesson_id=" LESSON-009 ",
        lesson_title=" Bai hoc thu 9 ",
        session=TeachingSession.MORNING,
        timetable_period=1,
        period_in_lesson=1,
    )


def test_context_preserves_scheduled_teaching_metadata():
    context = make_context()

    assert context.teaching_date == date(
        2026,
        9,
        28,
    )

    assert context.drafting_date == date(
        2026,
        9,
        27,
    )

    assert context.session is (
        TeachingSession.MORNING
    )

    assert context.curriculum_period == 9
    assert context.timetable_period == 1
    assert context.period_in_lesson == 1


def test_context_normalizes_text_fields():
    context = make_context()

    assert context.class_id == "6A1"
    assert context.subject_ref == "MATHEMATICS"
    assert context.component_ref == "ALGEBRA"
    assert context.lesson_id == "LESSON-009"
    assert context.lesson_title == "Bai hoc thu 9"


def test_context_allows_missing_drafting_date():
    context = make_context(
        drafting_date=None
    )

    assert context.drafting_date is None


def test_drafting_date_cannot_be_after_teaching_date():
    with pytest.raises(
        ValueError,
        match="must not be after",
    ):
        make_context(
            drafting_date=date(
                2026,
                9,
                29,
            )
        )


def test_context_is_frozen():
    context = make_context()

    with pytest.raises(
        FrozenInstanceError
    ):
        context.class_id = "6A2"
