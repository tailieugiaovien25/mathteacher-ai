from __future__ import annotations

from datetime import date
from typing import Any

from educational_planning_v2.models.academic_year_calendar_event import (
    AcademicYearCalendarEvent,
    AcademicYearCalendarEventStatus,
    AcademicYearCalendarEventType,
)
from educational_planning_v2.repositories.academic_year_calendar_event_repository import (
    AcademicYearCalendarEventRepository,
)


class SupabaseAcademicYearCalendarEventRepository(
    AcademicYearCalendarEventRepository
):
    TABLE_NAME = "academic_year_calendar_events"

    def __init__(
        self,
        *,
        client: Any,
    ) -> None:
        if client is None:
            raise ValueError(
                "client must not be None"
            )

        self._client = client

    def save(
        self,
        *,
        event: AcademicYearCalendarEvent,
    ) -> AcademicYearCalendarEvent:
        if not isinstance(
            event,
            AcademicYearCalendarEvent,
        ):
            raise TypeError(
                "event must be "
                "AcademicYearCalendarEvent"
            )

        payload = {
            "event_id": (
                event.event_id
            ),
            "academic_year_id": (
                event.academic_year_id
            ),
            "event_type": (
                event.event_type.value
            ),
            "name": (
                event.name
            ),
            "start_date": (
                event.start_date.isoformat()
            ),
            "end_date": (
                event.end_date.isoformat()
            ),
            "is_teaching_day_override": (
                event.is_teaching_day_override
            ),
            "note": (
                event.note
            ),
            "status": (
                event.status.value
            ),
        }

        response = (
            self._client
            .table(self.TABLE_NAME)
            .upsert(
                payload,
                on_conflict="event_id",
            )
            .execute()
        )

        rows = self._response_rows(
            response
        )

        if not rows:
            return event

        return self._from_row(
            rows[0]
        )

    def get(
        self,
        *,
        event_id: str,
    ) -> AcademicYearCalendarEvent | None:
        normalized_id = self._required_text(
            event_id,
            "event_id",
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "event_id",
                normalized_id,
            )
            .limit(1)
            .execute()
        )

        rows = self._response_rows(
            response
        )

        if not rows:
            return None

        return self._from_row(
            rows[0]
        )

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
        query = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
        )

        if academic_year_id is not None:
            query = query.eq(
                "academic_year_id",
                self._required_text(
                    academic_year_id,
                    "academic_year_id",
                ),
            )

        if event_type is not None:
            if not isinstance(
                event_type,
                AcademicYearCalendarEventType,
            ):
                raise TypeError(
                    "event_type must be "
                    "AcademicYearCalendarEventType "
                    "or None"
                )

            query = query.eq(
                "event_type",
                event_type.value,
            )

        if status is not None:
            if not isinstance(
                status,
                AcademicYearCalendarEventStatus,
            ):
                raise TypeError(
                    "status must be "
                    "AcademicYearCalendarEventStatus "
                    "or None"
                )

            query = query.eq(
                "status",
                status.value,
            )

        response = (
            query
            .order("start_date")
            .order("end_date")
            .order("name")
            .execute()
        )

        return tuple(
            self._from_row(row)
            for row in self._response_rows(
                response
            )
        )

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> AcademicYearCalendarEvent:
        note = row.get(
            "note"
        )

        return AcademicYearCalendarEvent(
            event_id=str(
                row["event_id"]
            ),
            academic_year_id=str(
                row["academic_year_id"]
            ),
            event_type=(
                AcademicYearCalendarEventType(
                    str(
                        row["event_type"]
                    )
                )
            ),
            name=str(
                row["name"]
            ),
            start_date=date.fromisoformat(
                str(
                    row["start_date"]
                )
            ),
            end_date=date.fromisoformat(
                str(
                    row["end_date"]
                )
            ),
            is_teaching_day_override=bool(
                row[
                    "is_teaching_day_override"
                ]
            ),
            note=(
                None
                if note is None
                else str(note)
            ),
            status=(
                AcademicYearCalendarEventStatus(
                    str(
                        row["status"]
                    )
                )
            ),
        )

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be str"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized

    @staticmethod
    def _response_rows(
        response: Any,
    ) -> list[dict[str, Any]]:
        data = getattr(
            response,
            "data",
            None,
        )

        if data is None:
            return []

        if not isinstance(
            data,
            list,
        ):
            raise TypeError(
                "Supabase response data must be a list"
            )

        if not all(
            isinstance(
                row,
                dict,
            )
            for row in data
        ):
            raise TypeError(
                "Supabase response rows must be dict"
            )

        return data
