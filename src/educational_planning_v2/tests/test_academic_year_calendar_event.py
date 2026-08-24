from datetime import date

import pytest

from educational_planning_v2.models.academic_year_calendar_event import (
    AcademicYearCalendarEvent,
    AcademicYearCalendarEventStatus,
    AcademicYearCalendarEventType,
)


def make_event(
    *,
    event_type=AcademicYearCalendarEventType.HOLIDAY,
    is_teaching_day_override=False,
    start_date=date(2026, 9, 2),
    end_date=date(2026, 9, 2),
):
    return AcademicYearCalendarEvent(
        event_id="event-1",
        academic_year_id="AY-2026-2027",
        event_type=event_type,
        name="Ng?y ngh?",
        start_date=start_date,
        end_date=end_date,
        is_teaching_day_override=(
            is_teaching_day_override
        ),
        note="Ghi ch?",
        status=(
            AcademicYearCalendarEventStatus.ACTIVE
        ),
    )


def test_regular_break_event_is_valid():
    event = make_event()

    assert event.event_id == "event-1"
    assert (
        event.event_type
        is AcademicYearCalendarEventType.HOLIDAY
    )
    assert event.is_teaching_day_override is False


def test_start_date_must_not_be_after_end_date():
    with pytest.raises(
        ValueError,
        match=(
            "start_date must not be after end_date"
        ),
    ):
        make_event(
            start_date=date(
                2026,
                9,
                3,
            ),
            end_date=date(
                2026,
                9,
                2,
            ),
        )


def test_makeup_day_requires_teaching_override():
    with pytest.raises(
        ValueError,
        match=(
            "MAKEUP_DAY must define "
            "is_teaching_day_override=True"
        ),
    ):
        make_event(
            event_type=(
                AcademicYearCalendarEventType.MAKEUP_DAY
            ),
            is_teaching_day_override=False,
        )


def test_makeup_day_with_override_is_valid():
    event = make_event(
        event_type=(
            AcademicYearCalendarEventType.MAKEUP_DAY
        ),
        is_teaching_day_override=True,
    )

    assert event.is_teaching_day_override is True


def test_non_makeup_event_cannot_define_teaching_override():
    with pytest.raises(
        ValueError,
        match=(
            "only MAKEUP_DAY may define "
            "is_teaching_day_override=True"
        ),
    ):
        make_event(
            event_type=(
                AcademicYearCalendarEventType.TET_BREAK
            ),
            is_teaching_day_override=True,
        )


def test_note_is_normalized():
    event = AcademicYearCalendarEvent(
        event_id="event-1",
        academic_year_id="AY-2026-2027",
        event_type=(
            AcademicYearCalendarEventType.OTHER_BREAK
        ),
        name="Ngh? kh?c",
        start_date=date(
            2026,
            10,
            1,
        ),
        end_date=date(
            2026,
            10,
            1,
        ),
        note="   Ghi ch? th?   ",
        status=(
            AcademicYearCalendarEventStatus.ACTIVE
        ),
    )

    assert event.note == "Ghi ch? th?"


def test_invalid_status_type_is_rejected():
    with pytest.raises(
        TypeError,
        match=(
            "status must be "
            "AcademicYearCalendarEventStatus"
        ),
    ):
        AcademicYearCalendarEvent(
            event_id="event-1",
            academic_year_id="AY-2026-2027",
            event_type=(
                AcademicYearCalendarEventType.HOLIDAY
            ),
            name="Ng?y ngh?",
            start_date=date(
                2026,
                9,
                2,
            ),
            end_date=date(
                2026,
                9,
                2,
            ),
            status="ACTIVE",
        )
