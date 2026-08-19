from datetime import date

import pytest

from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)
from educational_planning_v2.builders.weekly_schedule_input_builder import (
    WeeklyScheduleInputBuilder,
)
from educational_planning_v2.models.teacher_timetable import (
    TeacherTimetableSlot,
    TeacherTimetableSlotStatus,
    TeachingSession,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)


def make_assignment(
    *,
    assignment_id="assignment-1",
    owner_id="teacher-1",
    status=TeachingAssignmentStatus.ACTIVE,
):
    return TeachingAssignment(
        assignment_id=assignment_id,
        owner_id=owner_id,
        academic_year="2026-2027",
        class_id="6A1",
        role=TeachingAssignmentRole.TEACHING,
        subject_ref="TOAN",
        component_ref=None,
        effective_from=date(2026, 9, 1),
        effective_to=date(2027, 5, 31),
        status=status,
    )


def make_slot(
    *,
    assignment_id="assignment-1",
    owner_id="teacher-1",
    status=TeacherTimetableSlotStatus.ACTIVE,
):
    return TeacherTimetableSlot(
        slot_id="slot-1",
        owner_id=owner_id,
        academic_year="2026-2027",
        assignment_id=assignment_id,
        weekday=2,
        session=TeachingSession.MORNING,
        period=1,
        effective_from=date(2026, 9, 1),
        effective_to=date(2027, 5, 31),
        status=status,
    )


def test_builds_canonical_timetable_slot():
    builder = WeeklyScheduleInputBuilder()

    result = builder.build_timetable_slots(
        teacher_id="teacher-1",
        timetable_slots=(
            make_slot(),
        ),
        assignments=(
            make_assignment(),
        ),
    )

    assert len(result) == 1

    slot = result[0]

    assert slot.teacher_id == "teacher-1"
    assert slot.class_id == "6A1"
    assert slot.subject_ref == "TOAN"
    assert slot.component_ref is None
    assert slot.weekday == 2
    assert slot.timetable_period == 1


def test_inactive_timetable_slot_is_ignored():
    builder = WeeklyScheduleInputBuilder()

    result = builder.build_timetable_slots(
        teacher_id="teacher-1",
        timetable_slots=(
            make_slot(
                status=(
                    TeacherTimetableSlotStatus.INACTIVE
                ),
            ),
        ),
        assignments=(
            make_assignment(),
        ),
    )

    assert result == ()


def test_foreign_owner_slot_is_ignored():
    builder = WeeklyScheduleInputBuilder()

    result = builder.build_timetable_slots(
        teacher_id="teacher-1",
        timetable_slots=(
            make_slot(
                owner_id="teacher-2",
            ),
        ),
        assignments=(
            make_assignment(),
        ),
    )

    assert result == ()


def test_missing_assignment_is_rejected():
    builder = WeeklyScheduleInputBuilder()

    with pytest.raises(
        ValueError,
        match=(
            "missing active teaching assignment"
        ),
    ):
        builder.build_timetable_slots(
            teacher_id="teacher-1",
            timetable_slots=(
                make_slot(),
            ),
            assignments=(),
        )


def test_inactive_assignment_is_not_usable():
    builder = WeeklyScheduleInputBuilder()

    with pytest.raises(
        ValueError,
        match=(
            "missing active teaching assignment"
        ),
    ):
        builder.build_timetable_slots(
            teacher_id="teacher-1",
            timetable_slots=(
                make_slot(),
            ),
            assignments=(
                make_assignment(
                    status=(
                        TeachingAssignmentStatus.INACTIVE
                    ),
                ),
            ),
        )


def test_builder_rejects_non_tuple_inputs():
    builder = WeeklyScheduleInputBuilder()

    with pytest.raises(
        TypeError,
        match="timetable_slots must be a tuple",
    ):
        builder.build_timetable_slots(
            teacher_id="teacher-1",
            timetable_slots=[],
            assignments=(),
        )



def test_builds_curriculum_periods_from_scoped_ppct_rows():
    builder = WeeklyScheduleInputBuilder()

    result = builder.build_curriculum_periods(
        assignment=make_assignment(),
        ppct_rows=(
            PPCTRow(
                subject_grade="To?n 6",
                sub_subject="S? h?c",
                period=1,
                lesson_name="B?i m? ??u",
            ),
            PPCTRow(
                subject_grade="To?n 6",
                sub_subject="S? h?c",
                period=2,
                lesson_name="B?i m? ??u",
            ),
            PPCTRow(
                subject_grade="To?n 6",
                sub_subject="S? h?c",
                period=3,
                lesson_name="B?i ti?p theo",
            ),
        ),
    )

    assert len(result) == 3

    first = result[0]
    second = result[1]
    third = result[2]

    assert first.class_id == "6A1"
    assert first.subject_ref == "TOAN"
    assert first.period_number == 1
    assert first.lesson_title == "B?i m? ??u"

    assert (
        first.lesson_id
        == second.lesson_id
    )

    assert (
        first.lesson_id
        != third.lesson_id
    )

    assert first.period_in_lesson == 1
    assert second.period_in_lesson == 2

    assert first.total_lesson_periods == 2
    assert second.total_lesson_periods == 2

    assert third.period_in_lesson == 1
    assert third.total_lesson_periods == 1


def test_curriculum_periods_are_sorted_by_ppct_period():
    builder = WeeklyScheduleInputBuilder()

    result = builder.build_curriculum_periods(
        assignment=make_assignment(),
        ppct_rows=(
            PPCTRow(
                subject_grade="To?n 6",
                period=3,
                lesson_name="B?i 3",
            ),
            PPCTRow(
                subject_grade="To?n 6",
                period=1,
                lesson_name="B?i 1",
            ),
            PPCTRow(
                subject_grade="To?n 6",
                period=2,
                lesson_name="B?i 2",
            ),
        ),
    )

    assert tuple(
        item.period_number
        for item in result
    ) == (
        1,
        2,
        3,
    )


def test_duplicate_ppct_period_is_rejected():
    builder = WeeklyScheduleInputBuilder()

    with pytest.raises(
        ValueError,
        match="duplicate PPCT period",
    ):
        builder.build_curriculum_periods(
            assignment=make_assignment(),
            ppct_rows=(
                PPCTRow(
                    subject_grade="To?n 6",
                    period=1,
                    lesson_name="B?i A",
                ),
                PPCTRow(
                    subject_grade="To?n 6",
                    period=1,
                    lesson_name="B?i B",
                ),
            ),
        )


def test_curriculum_builder_rejects_non_tuple_rows():
    builder = WeeklyScheduleInputBuilder()

    with pytest.raises(
        TypeError,
        match="ppct_rows must be a tuple",
    ):
        builder.build_curriculum_periods(
            assignment=make_assignment(),
            ppct_rows=[],
        )
