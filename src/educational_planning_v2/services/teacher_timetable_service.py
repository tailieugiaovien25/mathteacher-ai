from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.models.teacher_timetable import (
    TeacherTimetableSlot,
    TeacherTimetableSlotStatus,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)
from educational_planning_v2.repositories.teacher_timetable_repository import (
    TeacherTimetableRepository,
)
from educational_planning_v2.repositories.teaching_assignment_repository import (
    TeachingAssignmentRepository,
)


@dataclass(frozen=True)
class TeacherTimetableSaveResult:
    slot: TeacherTimetableSlot


class TeacherTimetableService:
    def __init__(
        self,
        *,
        timetable_repository: TeacherTimetableRepository,
        assignment_repository: TeachingAssignmentRepository,
    ) -> None:
        self._timetable_repository = timetable_repository
        self._assignment_repository = assignment_repository

    def save_slot(
        self,
        *,
        slot: TeacherTimetableSlot,
    ) -> TeacherTimetableSaveResult:
        if not isinstance(
            slot,
            TeacherTimetableSlot,
        ):
            raise TypeError(
                "slot must be TeacherTimetableSlot"
            )

        assignment = (
            self._assignment_repository.get(
                assignment_id=slot.assignment_id,
            )
        )

        if assignment is None:
            raise ValueError(
                "teaching assignment not found"
            )

        if assignment.owner_id != slot.owner_id:
            raise ValueError(
                "teaching assignment owner mismatch"
            )

        if (
            assignment.academic_year
            != slot.academic_year
        ):
            raise ValueError(
                "teaching assignment academic year mismatch"
            )

        if (
            assignment.role
            is not TeachingAssignmentRole.TEACHING
        ):
            raise ValueError(
                "timetable slot requires TEACHING assignment"
            )

        if (
            assignment.status
            is not TeachingAssignmentStatus.ACTIVE
        ):
            raise ValueError(
                "timetable slot requires ACTIVE assignment"
            )

        if (
            slot.effective_from
            < assignment.effective_from
            or slot.effective_to
            > assignment.effective_to
        ):
            raise ValueError(
                "timetable slot effective range "
                "must be inside assignment range"
            )

        existing = (
            self._timetable_repository.find_position(
                owner_id=slot.owner_id,
                academic_year=slot.academic_year,
                weekday=slot.weekday,
                session=slot.session,
                period=slot.period,
                status=(
                    TeacherTimetableSlotStatus.ACTIVE
                ),
            )
        )

        for other in existing:
            if other.slot_id == slot.slot_id:
                continue

            if self._ranges_overlap(
                slot,
                other,
            ):
                raise ValueError(
                    "timetable position conflict"
                )

        saved = (
            self._timetable_repository.save(
                slot=slot
            )
        )

        return TeacherTimetableSaveResult(
            slot=saved
        )

    @staticmethod
    def _ranges_overlap(
        left: TeacherTimetableSlot,
        right: TeacherTimetableSlot,
    ) -> bool:
        return not (
            left.effective_to
            < right.effective_from
            or right.effective_to
            < left.effective_from
        )
