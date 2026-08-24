from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from educational_planning_v2.adapters.supabase_academic_year_calendar_event_repository import (
    SupabaseAcademicYearCalendarEventRepository,
)
from educational_planning_v2.models.academic_year_calendar_event import (
    AcademicYearCalendarEvent,
    AcademicYearCalendarEventStatus,
    AcademicYearCalendarEventType,
)


class FakeResponse:
    def __init__(
        self,
        data: Any,
    ) -> None:
        self.data = data


class FakeQuery:
    def __init__(
        self,
        rows: list[dict[str, Any]],
    ) -> None:
        self._rows = rows
        self._filters: list[
            tuple[str, Any]
        ] = []
        self._limit = None

    def select(
        self,
        columns: str,
    ) -> "FakeQuery":
        return self

    def eq(
        self,
        column: str,
        value: Any,
    ) -> "FakeQuery":
        self._filters.append(
            (
                column,
                value,
            )
        )
        return self

    def limit(
        self,
        value: int,
    ) -> "FakeQuery":
        self._limit = value
        return self

    def order(
        self,
        column: str,
    ) -> "FakeQuery":
        return self

    def upsert(
        self,
        payload: dict[str, Any],
        *,
        on_conflict: str,
    ) -> "FakeQuery":
        existing = None

        for row in self._rows:
            if (
                row.get(on_conflict)
                == payload[on_conflict]
            ):
                existing = row
                break

        if existing is None:
            self._rows.append(
                dict(payload)
            )
        else:
            existing.update(
                payload
            )

        self._filters = [
            (
                on_conflict,
                payload[on_conflict],
            )
        ]

        return self

    def execute(
        self,
    ) -> FakeResponse:
        rows = list(
            self._rows
        )

        for column, value in self._filters:
            rows = [
                row
                for row in rows
                if row.get(column) == value
            ]

        if self._limit is not None:
            rows = rows[
                : self._limit
            ]

        return FakeResponse(
            rows
        )


class FakeClient:
    def __init__(
        self,
        rows: list[dict[str, Any]],
    ) -> None:
        self.rows = rows

    def table(
        self,
        name: str,
    ) -> FakeQuery:
        assert (
            name
            == "academic_year_calendar_events"
        )

        return FakeQuery(
            self.rows
        )


def make_event(
    *,
    event_id="event-1",
    event_type=(
        AcademicYearCalendarEventType.HOLIDAY
    ),
    status=(
        AcademicYearCalendarEventStatus.ACTIVE
    ),
    is_teaching_day_override=False,
):
    return AcademicYearCalendarEvent(
        event_id=event_id,
        academic_year_id=(
            "AY-2026-2027"
        ),
        event_type=event_type,
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
        is_teaching_day_override=(
            is_teaching_day_override
        ),
        note="Ghi ch?",
        status=status,
    )


def test_save_and_get_event():
    repository = (
        SupabaseAcademicYearCalendarEventRepository(
            client=FakeClient(
                rows=[],
            ),
        )
    )

    saved = repository.save(
        event=make_event(),
    )

    loaded = repository.get(
        event_id="event-1",
    )

    assert saved == loaded
    assert loaded is not None
    assert (
        loaded.start_date
        == date(2026, 9, 2)
    )


def test_list_events_filters_academic_year():
    client = FakeClient(
        rows=[
            {
                "event_id": "event-1",
                "academic_year_id": (
                    "AY-2026-2027"
                ),
                "event_type": "HOLIDAY",
                "name": "Ng?y ngh?",
                "start_date": "2026-09-02",
                "end_date": "2026-09-02",
                "is_teaching_day_override": False,
                "note": None,
                "status": "ACTIVE",
            },
            {
                "event_id": "event-2",
                "academic_year_id": (
                    "AY-2025-2026"
                ),
                "event_type": "HOLIDAY",
                "name": "Ng?y ngh? kh?c",
                "start_date": "2025-09-02",
                "end_date": "2025-09-02",
                "is_teaching_day_override": False,
                "note": None,
                "status": "ACTIVE",
            },
        ],
    )

    repository = (
        SupabaseAcademicYearCalendarEventRepository(
            client=client,
        )
    )

    result = repository.list_events(
        academic_year_id=(
            "AY-2026-2027"
        ),
    )

    assert tuple(
        item.event_id
        for item in result
    ) == (
        "event-1",
    )


def test_list_events_filters_event_type():
    client = FakeClient(
        rows=[
            {
                "event_id": "event-1",
                "academic_year_id": (
                    "AY-2026-2027"
                ),
                "event_type": "HOLIDAY",
                "name": "Ng?y ngh?",
                "start_date": "2026-09-02",
                "end_date": "2026-09-02",
                "is_teaching_day_override": False,
                "note": None,
                "status": "ACTIVE",
            },
            {
                "event_id": "event-2",
                "academic_year_id": (
                    "AY-2026-2027"
                ),
                "event_type": "TET_BREAK",
                "name": "Ngh? T?t",
                "start_date": "2027-02-01",
                "end_date": "2027-02-07",
                "is_teaching_day_override": False,
                "note": None,
                "status": "ACTIVE",
            },
        ],
    )

    repository = (
        SupabaseAcademicYearCalendarEventRepository(
            client=client,
        )
    )

    result = repository.list_events(
        event_type=(
            AcademicYearCalendarEventType.TET_BREAK
        ),
    )

    assert tuple(
        item.event_id
        for item in result
    ) == (
        "event-2",
    )


def test_list_events_filters_status():
    client = FakeClient(
        rows=[
            {
                "event_id": "event-1",
                "academic_year_id": (
                    "AY-2026-2027"
                ),
                "event_type": "HOLIDAY",
                "name": "Ng?y ngh?",
                "start_date": "2026-09-02",
                "end_date": "2026-09-02",
                "is_teaching_day_override": False,
                "note": None,
                "status": "ACTIVE",
            },
            {
                "event_id": "event-2",
                "academic_year_id": (
                    "AY-2026-2027"
                ),
                "event_type": "OTHER_BREAK",
                "name": "Ngh? kh?c",
                "start_date": "2026-10-01",
                "end_date": "2026-10-01",
                "is_teaching_day_override": False,
                "note": None,
                "status": "INACTIVE",
            },
        ],
    )

    repository = (
        SupabaseAcademicYearCalendarEventRepository(
            client=client,
        )
    )

    result = repository.list_events(
        status=(
            AcademicYearCalendarEventStatus.ACTIVE
        ),
    )

    assert tuple(
        item.event_id
        for item in result
    ) == (
        "event-1",
    )


def test_makeup_day_maps_correctly():
    client = FakeClient(
        rows=[
            {
                "event_id": "event-1",
                "academic_year_id": (
                    "AY-2026-2027"
                ),
                "event_type": "MAKEUP_DAY",
                "name": "H?c b?",
                "start_date": "2026-09-12",
                "end_date": "2026-09-12",
                "is_teaching_day_override": True,
                "note": "H?c b? th? B?y",
                "status": "ACTIVE",
            },
        ],
    )

    repository = (
        SupabaseAcademicYearCalendarEventRepository(
            client=client,
        )
    )

    result = repository.list_events()

    assert len(result) == 1
    assert (
        result[0].event_type
        is AcademicYearCalendarEventType.MAKEUP_DAY
    )
    assert (
        result[0].is_teaching_day_override
        is True
    )


def test_invalid_event_type_filter_is_rejected():
    repository = (
        SupabaseAcademicYearCalendarEventRepository(
            client=FakeClient(
                rows=[],
            ),
        )
    )

    with pytest.raises(
        TypeError,
        match=(
            "event_type must be "
            "AcademicYearCalendarEventType "
            "or None"
        ),
    ):
        repository.list_events(
            event_type="HOLIDAY",
        )


def test_repository_requires_client():
    with pytest.raises(
        ValueError,
        match="client must not be None",
    ):
        SupabaseAcademicYearCalendarEventRepository(
            client=None,
        )
