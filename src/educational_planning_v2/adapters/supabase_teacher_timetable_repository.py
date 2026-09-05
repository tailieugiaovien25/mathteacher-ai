from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
import time

# V57E1_TRANSIENT_READ_RETRY
_TRANSIENT_READ_ERROR_NAMES = frozenset({
    "ConnectionTerminated", "ConnectionResetError", "ConnectError",
    "ReadError", "ReadTimeout", "RemoteProtocolError",
})

def _is_transient_read_error(error: BaseException) -> bool:
    current = error
    seen = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if type(current).__name__ in _TRANSIENT_READ_ERROR_NAMES:
            return True
        current = current.__cause__ or current.__context__
    return False


from educational_planning_v2.models.teacher_timetable import (
    TeacherTimetableSlot,
    TeacherTimetableSlotStatus,
    TeachingSession,
)
from educational_planning_v2.repositories.teacher_timetable_repository import (
    TeacherTimetableRepository,
)


class SupabaseTeacherTimetableRepository(
    TeacherTimetableRepository
):
    def __init__(
        self,
        client: Any,
        user_id: str,
        table_name: str = "teacher_timetable_slots",
    ) -> None:
        self._client = client
        self._user_id = self._required_text(
            user_id,
            "user_id",
        )
        self._table_name = self._required_text(
            table_name,
            "table_name",
        )

    def save(
        self,
        *,
        slot: TeacherTimetableSlot,
    ) -> TeacherTimetableSlot:
        if not isinstance(
            slot,
            TeacherTimetableSlot,
        ):
            raise TypeError(
                "slot must be TeacherTimetableSlot"
            )

        if slot.owner_id != self._user_id:
            raise ValueError(
                "slot owner does not match "
                "authenticated user"
            )

        row = {
            "slot_id": slot.slot_id,
            "owner_id": slot.owner_id,
            "academic_year": slot.academic_year,
            "assignment_id": slot.assignment_id,
            # V14B6K_TIMETABLE_COMPONENT_PERSISTENCE
            "component_id": slot.component_id,
            "weekday": slot.weekday,
            "session": slot.session.value,
            "period": slot.period,
            "effective_from": (
                slot.effective_from.isoformat()
            ),
            "effective_to": (
                slot.effective_to.isoformat()
            ),
            "status": slot.status.value,
            "updated_at": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
        }

        response = (
            self._client
            .table(self._table_name)
            .upsert(
                row,
                on_conflict="slot_id",
            )
            .execute()
        )

        rows = self._response_rows(
            response
        )

        return (
            self._from_row(rows[0])
            if rows
            else slot
        )

    def get(
        self,
        *,
        slot_id: str,
    ) -> TeacherTimetableSlot | None:
        normalized_id = self._required_text(
            slot_id,
            "slot_id",
        )

        response = (
            self._client
            .table(self._table_name)
            .select("*")
            .eq(
                "slot_id",
                normalized_id,
            )
            .eq(
                "owner_id",
                self._user_id,
            )
            .limit(1)
            .execute()
        )

        rows = self._response_rows(
            response
        )

        return (
            self._from_row(rows[0])
            if rows
            else None
        )

    def list_slots(
        self,
        *,
        owner_id: str,
        academic_year: str,
        status: TeacherTimetableSlotStatus | None = None,
    ) -> tuple[TeacherTimetableSlot, ...]:
        normalized_owner = self._required_text(
            owner_id,
            "owner_id",
        )

        normalized_year = self._required_text(
            academic_year,
            "academic_year",
        )

        self._require_owner(
            normalized_owner
        )

        if (
            status is not None
            and not isinstance(
                status,
                TeacherTimetableSlotStatus,
            )
        ):
            raise TypeError(
                "status must be "
                "TeacherTimetableSlotStatus or None"
            )

        query = (
            self._client
            .table(self._table_name)
            .select("*")
            .eq(
                "owner_id",
                normalized_owner,
            )
            .eq(
                "academic_year",
                normalized_year,
            )
        )

        if status is not None:
            query = query.eq(
                "status",
                status.value,
            )

        # V57E1_TRANSIENT_READ_RETRY
        # Retry once only for transport-level read failures.
        try:
            response = query.execute()
        except Exception as error:
            if not _is_transient_read_error(error):
                raise
            time.sleep(0.15)
            response = query.execute()

        rows = self._response_rows(
            response
        )

        return tuple(
            self._from_row(row)
            for row in rows
        )

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
        normalized_owner = self._required_text(
            owner_id,
            "owner_id",
        )

        normalized_year = self._required_text(
            academic_year,
            "academic_year",
        )

        self._require_owner(
            normalized_owner
        )

        if not isinstance(
            session,
            TeachingSession,
        ):
            raise TypeError(
                "session must be TeachingSession"
            )

        if (
            status is not None
            and not isinstance(
                status,
                TeacherTimetableSlotStatus,
            )
        ):
            raise TypeError(
                "status must be "
                "TeacherTimetableSlotStatus or None"
            )

        query = (
            self._client
            .table(self._table_name)
            .select("*")
            .eq(
                "owner_id",
                normalized_owner,
            )
            .eq(
                "academic_year",
                normalized_year,
            )
            .eq(
                "weekday",
                weekday,
            )
            .eq(
                "session",
                session.value,
            )
            .eq(
                "period",
                period,
            )
        )

        if status is not None:
            query = query.eq(
                "status",
                status.value,
            )

        rows = self._response_rows(
            query.execute()
        )

        return tuple(
            self._from_row(row)
            for row in rows
        )

    def delete(
        self,
        *,
        slot_id: str,
    ) -> None:
        normalized_id = self._required_text(
            slot_id,
            "slot_id",
        )

        (
            self._client
            .table(self._table_name)
            .delete()
            .eq(
                "slot_id",
                normalized_id,
            )
            .eq(
                "owner_id",
                self._user_id,
            )
            .execute()
        )

    def _require_owner(
        self,
        owner_id: str,
    ) -> None:
        if owner_id != self._user_id:
            raise ValueError(
                "owner_id does not match "
                "authenticated user"
            )

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> TeacherTimetableSlot:
        return TeacherTimetableSlot(
            slot_id=row["slot_id"],
            owner_id=row["owner_id"],
            academic_year=row["academic_year"],
            assignment_id=row["assignment_id"],
            component_id=(
                row.get("component_id")
                or None
            ),
            weekday=int(row["weekday"]),
            session=TeachingSession(
                row["session"]
            ),
            period=int(row["period"]),
            effective_from=date.fromisoformat(
                row["effective_from"]
            ),
            effective_to=date.fromisoformat(
                row["effective_to"]
            ),
            status=TeacherTimetableSlotStatus(
                row["status"]
            ),
        )

    @staticmethod
    def _response_rows(
        response: Any,
    ) -> list[dict[str, Any]]:
        rows = getattr(
            response,
            "data",
            None,
        )

        if rows is None:
            raise ValueError(
                "Supabase response does not contain data"
            )

        if not isinstance(
            rows,
            list,
        ):
            raise TypeError(
                "Supabase response data "
                "must be a list"
            )

        return rows

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
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized
