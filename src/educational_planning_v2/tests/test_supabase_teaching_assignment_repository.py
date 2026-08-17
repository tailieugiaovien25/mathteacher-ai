from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pytest

from educational_planning_v2.adapters.supabase_teaching_assignment_repository import (
    SupabaseTeachingAssignmentRepository,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
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
        assert on_conflict == "assignment_id"

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
            (
                column,
                value,
            )
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
                self.row["assignment_id"]
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
                row["assignment_id"]
                for row in rows
            }

            for assignment_id in ids:
                self.client.rows.pop(
                    assignment_id,
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
        assert name == "teaching_assignments"
        return FakeQuery(self)


def _assignment(
    assignment_id="assign-001",
    owner_id="user-1",
    class_id="6A2",
):
    return TeachingAssignment(
        assignment_id=assignment_id,
        owner_id=owner_id,
        academic_year="2026-2027",
        class_id=class_id,
        subject_ref="Toan",
        component_ref="So hoc",
        role=TeachingAssignmentRole.TEACHING,
        effective_from=date(2026, 9, 1),
        effective_to=date(2027, 5, 31),
        status=TeachingAssignmentStatus.ACTIVE,
    )


def test_save_get_list_and_delete():
    client = FakeClient()

    repository = (
        SupabaseTeachingAssignmentRepository(
            client,
            "user-1",
        )
    )

    repository.save(
        assignment=_assignment()
    )

    loaded = repository.get(
        assignment_id="assign-001"
    )

    assert loaded is not None
    assert loaded.class_id == "6A2"

    assignments = repository.list_assignments(
        owner_id="user-1",
        academic_year="2026-2027",
        role=TeachingAssignmentRole.TEACHING,
        status=TeachingAssignmentStatus.ACTIVE,
    )

    assert len(assignments) == 1

    repository.delete(
        assignment_id="assign-001"
    )

    assert (
        repository.get(
            assignment_id="assign-001"
        )
        is None
    )


def test_repository_blocks_cross_owner_save():
    repository = (
        SupabaseTeachingAssignmentRepository(
            FakeClient(),
            "user-1",
        )
    )

    with pytest.raises(ValueError):
        repository.save(
            assignment=_assignment(
                owner_id="user-2"
            )
        )


def test_repository_blocks_cross_owner_list():
    repository = (
        SupabaseTeachingAssignmentRepository(
            FakeClient(),
            "user-1",
        )
    )

    with pytest.raises(ValueError):
        repository.list_assignments(
            owner_id="user-2",
            academic_year="2026-2027",
        )


def test_migration_enables_owner_only_rls():
    root = Path(
        __file__
    ).resolve().parents[3]

    sql = (
        root
        / "supabase/migrations/"
        / "202608160003_teaching_assignments.sql"
    ).read_text(
        encoding="utf-8"
    ).lower()

    assert "enable row level security" in sql
    assert "to authenticated" in sql
    assert "auth.uid()" in sql
    assert "owner_id" in sql
    assert "service_role" not in sql


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("class_id", "6A1, 6A2"),
        ("subject_ref", "Toan, Ngu van"),
        ("component_ref", "Dai so; Hinh hoc"),
    ),
)
def test_repository_rejects_non_atomic_assignment_write(
    field_name,
    value,
):
    client = FakeClient()

    repository = (
        SupabaseTeachingAssignmentRepository(
            client,
            "user-1",
        )
    )

    assignment = _assignment()

    values = {
        "assignment_id":
            assignment.assignment_id,
        "owner_id":
            assignment.owner_id,
        "academic_year":
            assignment.academic_year,
        "class_id":
            assignment.class_id,
        "subject_ref":
            assignment.subject_ref,
        "component_ref":
            assignment.component_ref,
        "role":
            assignment.role,
        "effective_from":
            assignment.effective_from,
        "effective_to":
            assignment.effective_to,
        "status":
            assignment.status,
    }

    values[field_name] = value

    non_atomic = TeachingAssignment(
        **values
    )

    with pytest.raises(
        ValueError,
        match=field_name,
    ):
        repository.save(
            assignment=non_atomic,
        )

    assert client.rows == {}


def test_repository_can_read_legacy_non_atomic_assignment():
    client = FakeClient()

    client.rows["legacy-001"] = {
        "assignment_id": "legacy-001",
        "owner_id": "user-1",
        "academic_year": "2026-2027",
        "class_id": "6A1, 6A2",
        "subject_ref": "Toan",
        "component_ref": "Dai so, Hinh hoc",
        "role": "TEACHING",
        "effective_from": "2026-09-01",
        "effective_to": "2027-05-31",
        "status": "ACTIVE",
    }

    repository = (
        SupabaseTeachingAssignmentRepository(
            client,
            "user-1",
        )
    )

    loaded = repository.get(
        assignment_id="legacy-001",
    )

    assert loaded is not None
    assert loaded.class_id == "6A1, 6A2"
    assert (
        loaded.component_ref
        == "Dai so, Hinh hoc"
    )
