from __future__ import annotations

from typing import Any

import pytest

from educational_planning_v2.adapters.supabase_teacher_subject_assignment_repository import (
    SupabaseTeacherSubjectAssignmentRepository,
)
from educational_planning_v2.models.teacher_subject_assignment import (
    TeacherSubjectAssignment,
    TeacherSubjectAssignmentStatus,
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
                row.get("assignment_id")
                == payload["assignment_id"]
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
                "assignment_id",
                payload["assignment_id"],
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
            == "teacher_subject_assignments"
        )

        return FakeQuery(
            self.rows
        )


def make_assignment(
    *,
    assignment_id="tsa-1",
    teacher_id="teacher-1",
    academic_year="2026-2027",
    subject_id="SUBJECT-MATH",
    status=TeacherSubjectAssignmentStatus.ACTIVE,
):
    return TeacherSubjectAssignment(
        assignment_id=assignment_id,
        teacher_id=teacher_id,
        academic_year=academic_year,
        subject_id=subject_id,
        status=status,
    )


def test_save_and_get_assignment():
    client = FakeClient(
        rows=[],
    )

    repository = (
        SupabaseTeacherSubjectAssignmentRepository(
            client=client,
        )
    )

    saved = repository.save(
        assignment=make_assignment(),
    )

    loaded = repository.get(
        assignment_id="tsa-1",
    )

    assert saved == loaded
    assert loaded is not None
    assert (
        loaded.subject_id
        == "SUBJECT-MATH"
    )


def test_list_assignments_filters_teacher_and_year():
    client = FakeClient(
        rows=[
            {
                "assignment_id": "tsa-1",
                "teacher_id": "teacher-1",
                "academic_year": "2026-2027",
                "subject_id": "SUBJECT-MATH",
                "status": "ACTIVE",
            },
            {
                "assignment_id": "tsa-2",
                "teacher_id": "teacher-2",
                "academic_year": "2026-2027",
                "subject_id": "SUBJECT-MATH",
                "status": "ACTIVE",
            },
            {
                "assignment_id": "tsa-3",
                "teacher_id": "teacher-1",
                "academic_year": "2025-2026",
                "subject_id": "SUBJECT-MATH",
                "status": "ACTIVE",
            },
        ],
    )

    repository = (
        SupabaseTeacherSubjectAssignmentRepository(
            client=client,
        )
    )

    result = repository.list_assignments(
        teacher_id="teacher-1",
        academic_year="2026-2027",
    )

    assert tuple(
        item.assignment_id
        for item in result
    ) == (
        "tsa-1",
    )


def test_list_assignments_filters_status():
    client = FakeClient(
        rows=[
            {
                "assignment_id": "tsa-1",
                "teacher_id": "teacher-1",
                "academic_year": "2026-2027",
                "subject_id": "SUBJECT-MATH",
                "status": "ACTIVE",
            },
            {
                "assignment_id": "tsa-2",
                "teacher_id": "teacher-1",
                "academic_year": "2026-2027",
                "subject_id": "SUBJECT-ART",
                "status": "INACTIVE",
            },
        ],
    )

    repository = (
        SupabaseTeacherSubjectAssignmentRepository(
            client=client,
        )
    )

    result = repository.list_assignments(
        status=(
            TeacherSubjectAssignmentStatus.ACTIVE
        ),
    )

    assert tuple(
        item.assignment_id
        for item in result
    ) == (
        "tsa-1",
    )


def test_find_subject_scope_is_exact():
    client = FakeClient(
        rows=[
            {
                "assignment_id": "tsa-1",
                "teacher_id": "teacher-1",
                "academic_year": "2026-2027",
                "subject_id": "SUBJECT-MATH",
                "status": "ACTIVE",
            },
            {
                "assignment_id": "tsa-2",
                "teacher_id": "teacher-1",
                "academic_year": "2026-2027",
                "subject_id": "SUBJECT-ART",
                "status": "ACTIVE",
            },
        ],
    )

    repository = (
        SupabaseTeacherSubjectAssignmentRepository(
            client=client,
        )
    )

    result = repository.find_subject_scope(
        teacher_id="teacher-1",
        academic_year="2026-2027",
        subject_id="SUBJECT-MATH",
    )

    assert tuple(
        item.assignment_id
        for item in result
    ) == (
        "tsa-1",
    )


def test_invalid_status_filter_is_rejected():
    repository = (
        SupabaseTeacherSubjectAssignmentRepository(
            client=FakeClient(
                rows=[],
            ),
        )
    )

    with pytest.raises(
        TypeError,
        match=(
            "status must be "
            "TeacherSubjectAssignmentStatus "
            "or None"
        ),
    ):
        repository.list_assignments(
            status="ACTIVE",
        )


def test_repository_requires_client():
    with pytest.raises(
        ValueError,
        match="client must not be None",
    ):
        SupabaseTeacherSubjectAssignmentRepository(
            client=None,
        )
