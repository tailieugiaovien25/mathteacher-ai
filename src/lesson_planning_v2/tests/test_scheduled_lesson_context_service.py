from datetime import date

import pytest

from educational_planning_v2.models import (
    TeachingSession,
)
from lesson_planning_v2.services import (
    ScheduledLessonContextService,
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
        class_id="6A1",
        subject_ref="MATHEMATICS",
        component_ref="ALGEBRA",
        curriculum_period=9,
        lesson_id="LESSON-009",
        lesson_title="Bai hoc thu 9",
        period_in_lesson=1,
        teaching_equipment=(),
    )


def test_build_preserves_weekly_schedule_identity():
    context = (
        ScheduledLessonContextService()
        .build_from_weekly_schedule_row(
            make_row(),
            drafting_date=date(
                2026,
                9,
                27,
            ),
        )
    )

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

    assert context.class_id == "6A1"
    assert context.curriculum_period == 9
    assert context.lesson_id == "LESSON-009"


def test_build_preserves_session_and_timetable_period():
    context = (
        ScheduledLessonContextService()
        .build_from_weekly_schedule_row(
            make_row()
        )
    )

    assert (
        context.session
        is TeachingSession.AFTERNOON
    )

    assert context.timetable_period == 2
    assert context.period_in_lesson == 1


def test_build_allows_drafting_date_to_be_resolved_later():
    context = (
        ScheduledLessonContextService()
        .build_from_weekly_schedule_row(
            make_row()
        )
    )

    assert context.drafting_date is None


def test_service_does_not_import_ui_or_word_engine():
    import inspect

    module = inspect.getmodule(
        ScheduledLessonContextService
    )

    source = inspect.getsource(
        module
    )

    import_lines = tuple(
        line.strip().lower()
        for line in source.splitlines()
        if line.strip().startswith(
            ("import ", "from ")
        )
    )

    assert not any(
        "streamlit" in line
        for line in import_lines
    )

    assert not any(
        "docx" in line
        for line in import_lines
    )

    assert not any(
        "document_standardization" in line
        for line in import_lines
    )


def test_invalid_row_is_rejected():
    class InvalidRow:
        teaching_date = date(
            2026,
            9,
            28,
        )

    with pytest.raises(
        TypeError,
        match="missing required attribute",
    ):
        (
            ScheduledLessonContextService()
            .build_from_weekly_schedule_row(
                InvalidRow()
            )
        )
