from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from document_intelligence.contracts import (
    DocumentField,
)
from document_intelligence.lesson_plan_reviewed_schedule_row import (
    LessonPlanReviewedScheduleRow,
)
from educational_planning_v2.models.weekly_teaching_schedule import (
    TeachingSession,
)
from portal_v2.ui.weekly_schedule_portal import (
    WeeklySchedulePortalPreviewRow,
)


def make_row():
    return WeeklySchedulePortalPreviewRow(
        teaching_date=date(2026, 9, 28),
        weekday=1,
        timetable_period=2,
        session=TeachingSession.AFTERNOON,
        class_id="8A2",
        subject_ref="MATHEMATICS",
        component_ref="ALGEBRA",
        curriculum_period=9,
        lesson_id="LESSON-009",
        lesson_title="Đơn thức",
        period_in_lesson=1,
        teaching_equipment=(),
    )


def test_adapter_applies_teacher_resolved_metadata():
    original = make_row()

    reviewed = (
        LessonPlanReviewedScheduleRow
        .from_schedule_row(
            row=original,
            resolved_metadata={
                DocumentField.CLASS_NAME: "8A3",
                DocumentField.CURRICULUM_PERIOD: (
                    "10"
                ),
                DocumentField.LESSON_TITLE: (
                    "Đơn thức mới"
                ),
                DocumentField.TEACHING_DATE: (
                    "29/09/2026"
                ),
            },
        )
    )

    assert reviewed.class_id == "8A3"
    assert reviewed.curriculum_period == 10
    assert reviewed.lesson_title == "Đơn thức mới"
    assert reviewed.teaching_date == date(
        2026,
        9,
        29,
    )


def test_adapter_does_not_mutate_original_row():
    original = make_row()

    reviewed = (
        LessonPlanReviewedScheduleRow
        .from_schedule_row(
            row=original,
            resolved_metadata={
                DocumentField.CLASS_NAME: "8A3",
                DocumentField.LESSON_TITLE: (
                    "Đơn thức mới"
                ),
            },
        )
    )

    assert reviewed.class_id == "8A3"
    assert reviewed.lesson_title == "Đơn thức mới"

    assert original.class_id == "8A2"
    assert original.lesson_title == "Đơn thức"


def test_adapter_preserves_non_reviewed_schedule_metadata():
    original = make_row()

    reviewed = (
        LessonPlanReviewedScheduleRow
        .from_schedule_row(
            row=original,
            resolved_metadata={
                DocumentField.LESSON_TITLE: (
                    "Đơn thức mới"
                ),
            },
        )
    )

    assert (
        reviewed.subject_ref
        == original.subject_ref
    )
    assert (
        reviewed.component_ref
        == original.component_ref
    )
    assert (
        reviewed.lesson_id
        == original.lesson_id
    )
    assert (
        reviewed.session
        is original.session
    )
    assert (
        reviewed.timetable_period
        == original.timetable_period
    )
    assert (
        reviewed.period_in_lesson
        == original.period_in_lesson
    )


def test_adapter_falls_back_when_metadata_missing():
    original = make_row()

    reviewed = (
        LessonPlanReviewedScheduleRow
        .from_schedule_row(
            row=original,
            resolved_metadata={},
        )
    )

    assert reviewed.class_id == "8A2"
    assert reviewed.curriculum_period == 9
    assert reviewed.lesson_title == "Đơn thức"
    assert reviewed.teaching_date == date(
        2026,
        9,
        28,
    )


def test_adapter_rejects_invalid_curriculum_period():
    with pytest.raises(
        ValueError,
        match="must be an integer",
    ):
        (
            LessonPlanReviewedScheduleRow
            .from_schedule_row(
                row=make_row(),
                resolved_metadata={
                    DocumentField.CURRICULUM_PERIOD: (
                        "Tiết chín"
                    ),
                },
            )
        )


def test_adapter_is_frozen():
    reviewed = (
        LessonPlanReviewedScheduleRow
        .from_schedule_row(
            row=make_row(),
            resolved_metadata={},
        )
    )

    with pytest.raises(FrozenInstanceError):
        reviewed.class_id = "9A1"
