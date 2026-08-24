from datetime import date

from educational_planning_v2.models.weekly_teaching_schedule import (
    TeachingSession,
)
from document_intelligence.contracts import DocumentField
from document_intelligence.lesson_plan_reviewed_schedule_row import (
    LessonPlanReviewedScheduleRow,
)
from portal_v2.ui.weekly_schedule_portal import (
    WeeklySchedulePortalPreviewRow,
)


def make_schedule_row():
    return WeeklySchedulePortalPreviewRow(
        teaching_date=date(2026, 9, 28),
        weekday=1,
        timetable_period=2,
        session=TeachingSession.MORNING,
        class_id="8A1",
        subject_ref="TOAN",
        component_ref=None,
        curriculum_period=9,
        lesson_id="lesson-009",
        lesson_title="Đơn thức",
        period_in_lesson=1,
        teaching_equipment=(),
    )


def test_teacher_override_is_used_by_processing_row_without_mutating_schedule():
    schedule_row = make_schedule_row()

    resolved_metadata = {
        DocumentField.CLASS_NAME: "8A1",
        DocumentField.CURRICULUM_PERIOD: "9",
        DocumentField.LESSON_TITLE: "Đơn thức mới",
        DocumentField.TEACHING_DATE: "28/09/2026",
    }

    processing_row = (
        LessonPlanReviewedScheduleRow
        .from_schedule_row(
            row=schedule_row,
            resolved_metadata=resolved_metadata,
        )
    )

    assert processing_row.lesson_title == "Đơn thức mới"

    assert schedule_row.lesson_title == "Đơn thức"

    assert processing_row is not schedule_row

    assert processing_row.class_id == schedule_row.class_id
    assert (
        processing_row.curriculum_period
        == schedule_row.curriculum_period
    )
    assert (
        processing_row.teaching_date
        == schedule_row.teaching_date
    )


def test_reviewed_processing_row_preserves_schedule_identity():
    schedule_row = make_schedule_row()

    processing_row = (
        LessonPlanReviewedScheduleRow
        .from_schedule_row(
            row=schedule_row,
            resolved_metadata={
                DocumentField.LESSON_TITLE:
                    "Đơn thức mới",
            },
        )
    )

    assert (
        processing_row.timetable_period
        == schedule_row.timetable_period
    )
    assert processing_row.session == schedule_row.session
    assert (
        processing_row.subject_ref
        == schedule_row.subject_ref
    )
    assert (
        processing_row.component_ref
        == schedule_row.component_ref
    )
    assert processing_row.lesson_id == schedule_row.lesson_id
    assert (
        processing_row.period_in_lesson
        == schedule_row.period_in_lesson
    )
    assert (
        processing_row.teaching_equipment
        == schedule_row.teaching_equipment
    )
