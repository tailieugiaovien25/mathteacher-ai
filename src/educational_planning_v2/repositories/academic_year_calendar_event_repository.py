from __future__ import annotations

from abc import ABC, abstractmethod

from educational_planning_v2.models.academic_year_calendar_event import (
    AcademicYearCalendarEvent,
    AcademicYearCalendarEventStatus,
    AcademicYearCalendarEventType,
)


class AcademicYearCalendarEventRepository(
    ABC
):
    @abstractmethod
    def save(
        self,
        *,
        event: AcademicYearCalendarEvent,
    ) -> AcademicYearCalendarEvent:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        *,
        event_id: str,
    ) -> AcademicYearCalendarEvent | None:
        raise NotImplementedError

    @abstractmethod
    def list_events(
        self,
        *,
        academic_year_id: str | None = None,
        event_type: AcademicYearCalendarEventType | None = None,
        status: AcademicYearCalendarEventStatus | None = None,
    ) -> tuple[
        AcademicYearCalendarEvent,
        ...,
    ]:
        raise NotImplementedError
