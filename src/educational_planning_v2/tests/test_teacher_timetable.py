from datetime import date

import pytest

from educational_planning_v2.models.teacher_timetable import (
    TeacherTimetableSlot,
    TeacherTimetableSlotStatus,
    TeachingSession,
)


def _slot(**changes):
    values = {
        "slot_id": "slot-001",
        "owner_id": "teacher-001",
        "academic_year": "2026-2027",
        "assignment_id": "assign-001",
        "weekday": 1,
        "session": TeachingSession.MORNING,
        "period": 1,
        "effective_from": date(2026, 9, 1),
        "effective_to": date(2027, 5, 31),
        "status": TeacherTimetableSlotStatus.ACTIVE,
    }

    values.update(changes)

    return TeacherTimetableSlot(**values)


def test_teacher_timetable_slot_normalizes_text():
    slot = _slot(
        slot_id=" slot-001 ",
        owner_id=" teacher-001 ",
        academic_year=" 2026-2027 ",
        assignment_id=" assign-001 ",
    )

    assert slot.slot_id == "slot-001"
    assert slot.owner_id == "teacher-001"
    assert slot.academic_year == "2026-2027"
    assert slot.assignment_id == "assign-001"


def test_teacher_timetable_position_key():
    slot = _slot(
        weekday=7,
        session=TeachingSession.AFTERNOON,
        period=5,
    )

    assert slot.position_key == (
        7,
        TeachingSession.AFTERNOON,
        5,
    )


@pytest.mark.parametrize(
    "weekday",
    (0, 8),
)
def test_weekday_must_be_between_1_and_7(
    weekday,
):
    with pytest.raises(ValueError):
        _slot(
            weekday=weekday,
        )


@pytest.mark.parametrize(
    "period",
    (0, 6),
)
def test_period_must_be_between_1_and_5(
    period,
):
    with pytest.raises(ValueError):
        _slot(
            period=period,
        )


def test_weekday_bool_blocked():
    with pytest.raises(TypeError):
        _slot(
            weekday=True,
        )


def test_period_bool_blocked():
    with pytest.raises(TypeError):
        _slot(
            period=False,
        )


def test_session_type_required():
    with pytest.raises(TypeError):
        _slot(
            session="MORNING",
        )


def test_status_type_required():
    with pytest.raises(TypeError):
        _slot(
            status="ACTIVE",
        )


def test_invalid_effective_range_blocked():
    with pytest.raises(ValueError):
        _slot(
            effective_from=date(2027, 6, 1),
            effective_to=date(2026, 9, 1),
        )


def test_sunday_afternoon_period_five_supported():
    slot = _slot(
        weekday=7,
        session=TeachingSession.AFTERNOON,
        period=5,
    )

    assert slot.weekday == 7
    assert slot.session is TeachingSession.AFTERNOON
    assert slot.period == 5
