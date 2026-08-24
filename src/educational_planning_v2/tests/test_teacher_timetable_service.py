from datetime import date

import pytest

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
from educational_planning_v2.services.teacher_timetable_service import (
    TeacherTimetableService,
)


class MemoryAssignmentRepository:
    def __init__(self, assignments):
        self.assignments = {
            item.assignment_id: item
            for item in assignments
        }

    def get(
        self,
        *,
        assignment_id,
    ):
        return self.assignments.get(
            assignment_id
        )


class MemoryTimetableRepository:
    def __init__(self):
        self.slots = {}

    def save(
        self,
        *,
        slot,
    ):
        self.slots[
            slot.slot_id
        ] = slot
        return slot

    def find_position(
        self,
        *,
        owner_id,
        academic_year,
        weekday,
        session,
        period,
        status=None,
    ):
        result = []

        for slot in self.slots.values():
            if slot.owner_id != owner_id:
                continue

            if (
                slot.academic_year
                != academic_year
            ):
                continue

            if slot.weekday != weekday:
                continue

            if slot.session is not session:
                continue

            if slot.period != period:
                continue

            if (
                status is not None
                and slot.status is not status
            ):
                continue

            result.append(slot)

        return tuple(result)


def _assignment(
    *,
    assignment_id="assign-001",
    role=TeachingAssignmentRole.TEACHING,
    status=TeachingAssignmentStatus.ACTIVE,
    effective_from=date(2026, 9, 1),
    effective_to=date(2027, 5, 31),
):
    return TeachingAssignment(
        assignment_id=assignment_id,
        owner_id="teacher-001",
        academic_year="2026-2027",
        class_id="6A1",
        subject_ref=(
            "Toan"
            if role is TeachingAssignmentRole.TEACHING
            else None
        ),
        component_ref=None,
        role=role,
        effective_from=effective_from,
        effective_to=effective_to,
        status=status,
    )


def _slot(
    *,
    slot_id="slot-001",
    assignment_id="assign-001",
    weekday=1,
    session=TeachingSession.MORNING,
    period=1,
    effective_from=date(2026, 9, 1),
    effective_to=date(2027, 5, 31),
):
    return TeacherTimetableSlot(
        slot_id=slot_id,
        owner_id="teacher-001",
        academic_year="2026-2027",
        assignment_id=assignment_id,
        weekday=weekday,
        session=session,
        period=period,
        effective_from=effective_from,
        effective_to=effective_to,
        status=(
            TeacherTimetableSlotStatus.ACTIVE
        ),
    )


def _service(
    assignment,
):
    timetable_repository = (
        MemoryTimetableRepository()
    )

    service = TeacherTimetableService(
        timetable_repository=(
            timetable_repository
        ),
        assignment_repository=(
            MemoryAssignmentRepository(
                [assignment]
            )
        ),
    )

    return (
        service,
        timetable_repository,
    )


def test_save_valid_slot():
    service, repository = _service(
        _assignment()
    )

    result = service.save_slot(
        slot=_slot()
    )

    assert result.slot.slot_id == "slot-001"
    assert "slot-001" in repository.slots


def test_conflicting_position_overlap_blocked():
    service, _ = _service(
        _assignment()
    )

    service.save_slot(
        slot=_slot(
            slot_id="slot-001",
        )
    )

    with pytest.raises(
        ValueError,
        match="timetable position conflict",
    ):
        service.save_slot(
            slot=_slot(
                slot_id="slot-002",
            )
        )


def test_same_period_different_session_allowed():
    service, _ = _service(
        _assignment()
    )

    service.save_slot(
        slot=_slot(
            slot_id="slot-morning",
            session=TeachingSession.MORNING,
        )
    )

    result = service.save_slot(
        slot=_slot(
            slot_id="slot-afternoon",
            session=TeachingSession.AFTERNOON,
        )
    )

    assert (
        result.slot.session
        is TeachingSession.AFTERNOON
    )


def test_same_session_different_period_allowed():
    service, _ = _service(
        _assignment()
    )

    service.save_slot(
        slot=_slot(
            slot_id="slot-1",
            period=1,
        )
    )

    result = service.save_slot(
        slot=_slot(
            slot_id="slot-2",
            period=2,
        )
    )

    assert result.slot.period == 2


def test_same_position_non_overlapping_ranges_allowed():
    assignment = _assignment(
        effective_from=date(2026, 9, 1),
        effective_to=date(2027, 5, 31),
    )

    service, _ = _service(
        assignment
    )

    service.save_slot(
        slot=_slot(
            slot_id="slot-old",
            effective_from=date(2026, 9, 1),
            effective_to=date(2026, 12, 31),
        )
    )

    result = service.save_slot(
        slot=_slot(
            slot_id="slot-new",
            effective_from=date(2027, 1, 1),
            effective_to=date(2027, 5, 31),
        )
    )

    assert result.slot.slot_id == "slot-new"


def test_inactive_assignment_blocked():
    service, _ = _service(
        _assignment(
            status=(
                TeachingAssignmentStatus.INACTIVE
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="requires ACTIVE assignment",
    ):
        service.save_slot(
            slot=_slot()
        )


def test_homeroom_assignment_blocked():
    assignment = _assignment(
        role=TeachingAssignmentRole.HOMEROOM,
    )

    service, _ = _service(
        assignment
    )

    with pytest.raises(
        ValueError,
        match="requires TEACHING assignment",
    ):
        service.save_slot(
            slot=_slot()
        )


def test_slot_range_must_be_inside_assignment_range():
    service, _ = _service(
        _assignment(
            effective_from=date(2026, 9, 1),
            effective_to=date(2027, 5, 31),
        )
    )

    with pytest.raises(
        ValueError,
        match="must be inside assignment range",
    ):
        service.save_slot(
            slot=_slot(
                effective_from=date(2026, 8, 1),
                effective_to=date(2027, 5, 31),
            )
        )


def test_missing_assignment_blocked():
    service = TeacherTimetableService(
        timetable_repository=(
            MemoryTimetableRepository()
        ),
        assignment_repository=(
            MemoryAssignmentRepository([])
        ),
    )

    with pytest.raises(
        ValueError,
        match="teaching assignment not found",
    ):
        service.save_slot(
            slot=_slot()
        )
