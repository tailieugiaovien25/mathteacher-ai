from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pytest

from educational_planning_v2.adapters.supabase_teacher_timetable_repository import (
    SupabaseTeacherTimetableRepository,
)
from educational_planning_v2.models.teacher_timetable import (
    TeacherTimetableSlot,
    TeacherTimetableSlotStatus,
    TeachingSession,
)


@dataclass
class Response:
    data: list


class FakeQuery:
    def __init__(self, client):
        self.client = client
        self.operation = None
        self.row = None
        self.filters = []

    def upsert(
        self,
        row,
        on_conflict,
    ):
        assert on_conflict == "slot_id"

        self.operation = "upsert"
        self.row = row
        return self

    def select(
        self,
        columns,
    ):
        self.operation = "select"
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(
        self,
        column,
        value,
    ):
        self.filters.append(
            (column, value)
        )
        return self

    def limit(
        self,
        value,
    ):
        return self

    def execute(self):
        if self.operation == "upsert":
            self.client.rows[
                self.row["slot_id"]
            ] = dict(self.row)

            return Response(
                [dict(self.row)]
            )

        rows = list(
            self.client.rows.values()
        )

        for column, value in self.filters:
            rows = [
                row
                for row in rows
                if row.get(column) == value
            ]

        if self.operation == "delete":
            ids = {
                row["slot_id"]
                for row in rows
            }

            for slot_id in ids:
                self.client.rows.pop(
                    slot_id,
                    None,
                )

            return Response([])

        return Response(rows)


class FakeClient:
    def __init__(self):
        self.rows = {}

    def table(
        self,
        name,
    ):
        assert name == "teacher_timetable_slots"
        return FakeQuery(self)


def _slot(
    *,
    slot_id="slot-001",
    owner_id="user-1",
    assignment_id="assign-001",
    weekday=1,
    session=TeachingSession.MORNING,
    period=1,
    status=TeacherTimetableSlotStatus.ACTIVE,
):
    return TeacherTimetableSlot(
        slot_id=slot_id,
        owner_id=owner_id,
        academic_year="2026-2027",
        assignment_id=assignment_id,
        weekday=weekday,
        session=session,
        period=period,
        effective_from=date(2026, 9, 1),
        effective_to=date(2027, 5, 31),
        status=status,
    )


def test_save_get_list_find_and_delete():
    client = FakeClient()

    repository = (
        SupabaseTeacherTimetableRepository(
            client,
            "user-1",
        )
    )

    saved = repository.save(
        slot=_slot()
    )

    assert saved.slot_id == "slot-001"

    loaded = repository.get(
        slot_id="slot-001"
    )

    assert loaded is not None
    assert loaded.assignment_id == "assign-001"
    assert loaded.weekday == 1
    assert loaded.session is TeachingSession.MORNING
    assert loaded.period == 1

    slots = repository.list_slots(
        owner_id="user-1",
        academic_year="2026-2027",
        status=TeacherTimetableSlotStatus.ACTIVE,
    )

    assert len(slots) == 1

    position = repository.find_position(
        owner_id="user-1",
        academic_year="2026-2027",
        weekday=1,
        session=TeachingSession.MORNING,
        period=1,
        status=TeacherTimetableSlotStatus.ACTIVE,
    )

    assert len(position) == 1
    assert position[0].slot_id == "slot-001"

    repository.delete(
        slot_id="slot-001"
    )

    assert (
        repository.get(
            slot_id="slot-001"
        )
        is None
    )


def test_repository_supports_sunday_afternoon_period_five():
    repository = (
        SupabaseTeacherTimetableRepository(
            FakeClient(),
            "user-1",
        )
    )

    repository.save(
        slot=_slot(
            slot_id="slot-sunday",
            weekday=7,
            session=TeachingSession.AFTERNOON,
            period=5,
        )
    )

    found = repository.find_position(
        owner_id="user-1",
        academic_year="2026-2027",
        weekday=7,
        session=TeachingSession.AFTERNOON,
        period=5,
    )

    assert len(found) == 1
    assert found[0].weekday == 7
    assert found[0].period == 5


def test_repository_blocks_cross_owner_save():
    repository = (
        SupabaseTeacherTimetableRepository(
            FakeClient(),
            "user-1",
        )
    )

    with pytest.raises(ValueError):
        repository.save(
            slot=_slot(
                owner_id="user-2",
            )
        )


def test_repository_blocks_cross_owner_list():
    repository = (
        SupabaseTeacherTimetableRepository(
            FakeClient(),
            "user-1",
        )
    )

    with pytest.raises(ValueError):
        repository.list_slots(
            owner_id="user-2",
            academic_year="2026-2027",
        )


def test_repository_blocks_cross_owner_position_lookup():
    repository = (
        SupabaseTeacherTimetableRepository(
            FakeClient(),
            "user-1",
        )
    )

    with pytest.raises(ValueError):
        repository.find_position(
            owner_id="user-2",
            academic_year="2026-2027",
            weekday=1,
            session=TeachingSession.MORNING,
            period=1,
        )


def test_invalid_session_filter_blocked():
    repository = (
        SupabaseTeacherTimetableRepository(
            FakeClient(),
            "user-1",
        )
    )

    with pytest.raises(TypeError):
        repository.find_position(
            owner_id="user-1",
            academic_year="2026-2027",
            weekday=1,
            session="MORNING",
            period=1,
        )


def test_migration_contains_rls_and_assignment_fk():
    root = Path(
        __file__
    ).resolve().parents[3]

    sql = (
        root
        / "supabase/migrations/"
        / "202608160004_teacher_timetable_slots.sql"
    ).read_text(
        encoding="utf-8"
    ).lower()

    assert "teacher_timetable_slots" in sql
    assert "references public.teaching_assignments" in sql
    assert "enable row level security" in sql
    assert "auth.uid()" in sql
    assert "weekday between 1 and 7" in sql
    assert "period between 1 and 5" in sql
    assert "'morning'" in sql
    assert "'afternoon'" in sql
