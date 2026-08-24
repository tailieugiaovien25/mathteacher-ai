from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from educational_planning_v2.adapters.supabase_admin_teaching_assignment_repository import (
    SupabaseAdminTeachingAssignmentRepository,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
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
        self._delete_mode = False

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

    def delete(
        self,
    ) -> "FakeQuery":
        self._delete_mode = True
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

        if self._delete_mode:
            ids_to_remove = {
                row["assignment_id"]
                for row in rows
            }

            self._rows[:] = [
                row
                for row in self._rows
                if (
                    row["assignment_id"]
                    not in ids_to_remove
                )
            ]

            return FakeResponse(
                []
            )

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
            == "teaching_assignments"
        )

        return FakeQuery(
            self.rows
        )


def make_assignment(
    *,
    assignment_id="assign-1",
    owner_id="teacher-1",
    status=TeachingAssignmentStatus.ACTIVE,
):
    return TeachingAssignment(
        assignment_id=assignment_id,
        owner_id=owner_id,
        academic_year="2026-2027",
        class_id="6A1",
        subject_ref="subject-math",
        component_ref="component-algebra",
        role=TeachingAssignmentRole.TEACHING,
        effective_from=date(
            2026,
            8,
            24,
        ),
        effective_to=date(
            2027,
            5,
            31,
        ),
        status=status,
    )


def test_admin_can_save_assignment_for_any_teacher():
    repository = (
        SupabaseAdminTeachingAssignmentRepository(
            client=FakeClient(
                rows=[],
            ),
        )
    )

    saved = repository.save(
        assignment=(
            make_assignment(
                owner_id="teacher-2"
            )
        )
    )

    assert (
        saved.owner_id
        == "teacher-2"
    )


def test_admin_can_get_assignment_without_owner_scope():
    client = FakeClient(
        rows=[
            {
                "assignment_id": "assign-1",
                "owner_id": "teacher-9",
                "academic_year": "2026-2027",
                "class_id": "6A1",
                "subject_ref": "subject-math",
                "component_ref": "component-algebra",
                "role": "TEACHING",
                "effective_from": "2026-08-24",
                "effective_to": "2027-05-31",
                "status": "ACTIVE",
            },
        ],
    )

    repository = (
        SupabaseAdminTeachingAssignmentRepository(
            client=client,
        )
    )

    assignment = repository.get(
        assignment_id="assign-1",
    )

    assert assignment is not None
    assert (
        assignment.owner_id
        == "teacher-9"
    )


def test_admin_can_list_all_assignments():
    client = FakeClient(
        rows=[
            {
                "assignment_id": "assign-1",
                "owner_id": "teacher-1",
                "academic_year": "2026-2027",
                "class_id": "6A1",
                "subject_ref": "subject-math",
                "component_ref": None,
                "role": "TEACHING",
                "effective_from": "2026-08-24",
                "effective_to": "2027-05-31",
                "status": "ACTIVE",
            },
            {
                "assignment_id": "assign-2",
                "owner_id": "teacher-2",
                "academic_year": "2026-2027",
                "class_id": "7A1",
                "subject_ref": None,
                "component_ref": None,
                "role": "HOMEROOM",
                "effective_from": "2026-08-24",
                "effective_to": "2027-05-31",
                "status": "ACTIVE",
            },
        ],
    )

    repository = (
        SupabaseAdminTeachingAssignmentRepository(
            client=client,
        )
    )

    result = (
        repository.list_assignments()
    )

    assert len(result) == 2


def test_admin_can_filter_by_teacher_and_year():
    client = FakeClient(
        rows=[
            {
                "assignment_id": "assign-1",
                "owner_id": "teacher-1",
                "academic_year": "2026-2027",
                "class_id": "6A1",
                "subject_ref": "subject-math",
                "component_ref": None,
                "role": "TEACHING",
                "effective_from": "2026-08-24",
                "effective_to": "2027-05-31",
                "status": "ACTIVE",
            },
            {
                "assignment_id": "assign-2",
                "owner_id": "teacher-2",
                "academic_year": "2026-2027",
                "class_id": "7A1",
                "subject_ref": "subject-english",
                "component_ref": None,
                "role": "TEACHING",
                "effective_from": "2026-08-24",
                "effective_to": "2027-05-31",
                "status": "ACTIVE",
            },
        ],
    )

    repository = (
        SupabaseAdminTeachingAssignmentRepository(
            client=client,
        )
    )

    result = repository.list_assignments(
        owner_id="teacher-2",
        academic_year="2026-2027",
    )

    assert len(result) == 1
    assert (
        result[0].owner_id
        == "teacher-2"
    )


def test_admin_can_delete_assignment():
    rows = [
        {
            "assignment_id": "assign-1",
            "owner_id": "teacher-1",
            "academic_year": "2026-2027",
            "class_id": "6A1",
            "subject_ref": "subject-math",
            "component_ref": None,
            "role": "TEACHING",
            "effective_from": "2026-08-24",
            "effective_to": "2027-05-31",
            "status": "ACTIVE",
        },
    ]

    repository = (
        SupabaseAdminTeachingAssignmentRepository(
            client=FakeClient(
                rows=rows,
            ),
        )
    )

    repository.delete(
        assignment_id="assign-1",
    )

    assert rows == []


def test_repository_requires_client():
    with pytest.raises(
        ValueError,
        match="client must not be None",
    ):
        SupabaseAdminTeachingAssignmentRepository(
            client=None,
        )
