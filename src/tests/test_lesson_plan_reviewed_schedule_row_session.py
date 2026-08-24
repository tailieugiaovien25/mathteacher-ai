from datetime import date
from types import SimpleNamespace

from document_intelligence.lesson_plan_reviewed_schedule_row import (
    LessonPlanReviewedScheduleRow,
)
from educational_planning_v2.models.teacher_timetable import (
    TeachingSession,
)


def _source_row(session):
    return SimpleNamespace(
        teaching_date=date(
            2026,
            9,
            28,
        ),
        weekday=1,
        timetable_period=1,
        session=session,
        class_id="6A1",
        subject_ref="MATHEMATICS",
        component_ref=None,
        curriculum_period=9,
        lesson_id="LESSON-009",
        lesson_title="B\u00e0i h\u1ecdc 9",
        period_in_lesson=1,
        total_lesson_periods=1,
        teaching_equipment=(),
    )


def _build(session):
    return (
        LessonPlanReviewedScheduleRow
        .from_schedule_row(
            row=_source_row(session),
            resolved_metadata={},
        )
    )


def test_reviewed_row_preserves_session_enum():
    result = _build(
        TeachingSession.MORNING
    )

    assert (
        result.session
        is TeachingSession.MORNING
    )


def test_reviewed_row_accepts_canonical_session_value():
    result = _build(
        "MORNING"
    )

    assert (
        result.session
        is TeachingSession.MORNING
    )


def test_reviewed_row_accepts_legacy_enum_string():
    result = _build(
        "TeachingSession.MORNING"
    )

    assert (
        result.session
        is TeachingSession.MORNING
    )
