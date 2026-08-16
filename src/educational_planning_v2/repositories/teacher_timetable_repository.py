from __future__ import annotations

from abc import ABC, abstractmethod

from educational_planning_v2.models.teacher_timetable import (
    TeacherTimetableSlot,
    TeacherTimetableSlotStatus,
    TeachingSession,
)


class TeacherTimetableRepository(ABC):
    """
    Storage-neutral repository for teacher timetable slots.

    One slot represents one timetable position:
    weekday + session + period,
    linked to one TeachingAssignment.
    """

    @abstractmethod
    def save(
        self,
        *,
        slot: TeacherTimetableSlot,
    ) -> TeacherTimetableSlot:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        *,
        slot_id: str,
    ) -> TeacherTimetableSlot | None:
        raise NotImplementedError

    @abstractmethod
    def list_slots(
        self,
        *,
        owner_id: str,
        academic_year: str,
        status: TeacherTimetableSlotStatus | None = None,
    ) -> tuple[TeacherTimetableSlot, ...]:
        raise NotImplementedError

    @abstractmethod
    def find_position(
        self,
        *,
        owner_id: str,
        academic_year: str,
        weekday: int,
        session: TeachingSession,
        period: int,
        status: TeacherTimetableSlotStatus | None = None,
    ) -> tuple[TeacherTimetableSlot, ...]:
        """
        Return timetable slots occupying one logical position.

        The service layer will later decide whether overlapping
        effective-date ranges are legal.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        *,
        slot_id: str,
    ) -> None:
        raise NotImplementedError
