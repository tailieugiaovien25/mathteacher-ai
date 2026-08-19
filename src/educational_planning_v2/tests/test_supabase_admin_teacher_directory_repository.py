from __future__ import annotations

from typing import Any

from educational_planning_v2.adapters.supabase_admin_teacher_directory_repository import (
    SupabaseAdminTeacherDirectoryRepository,
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

    def select(
        self,
        columns: str,
    ) -> "FakeQuery":
        return self

    def execute(
        self,
    ) -> FakeResponse:
        return FakeResponse(
            list(self._rows)
        )


class FakeClient:
    def __init__(
        self,
        *,
        profiles: list[dict[str, Any]],
    ) -> None:
        self._profiles = profiles

    def table(
        self,
        name: str,
    ) -> FakeQuery:
        assert name == "teacher_profiles"

        return FakeQuery(
            self._profiles
        )


def test_list_teachers_returns_all_teacher_profiles():
    client = FakeClient(
        profiles=[
            {
                "user_id": "teacher-1",
                "teacher_code": "GV001",
                "full_name": "Nguyen Van B",
                "school_name": "School A",
            },
            {
                "user_id": "teacher-2",
                "teacher_code": "GV002",
                "full_name": "Nguyen Van A",
                "school_name": "School B",
            },
        ],
    )

    repository = (
        SupabaseAdminTeacherDirectoryRepository(
            client=client,
        )
    )

    result = repository.list_teachers()

    assert tuple(
        item.user_id
        for item in result
    ) == (
        "teacher-2",
        "teacher-1",
    )


def test_portal_role_is_not_required_for_teacher_identity():
    client = FakeClient(
        profiles=[
            {
                "user_id": "admin-user",
                "teacher_code": "GV001",
                "full_name": "Admin Teacher",
                "school_name": "School A",
            },
        ],
    )

    repository = (
        SupabaseAdminTeacherDirectoryRepository(
            client=client,
        )
    )

    result = repository.list_teachers()

    assert len(result) == 1
    assert result[0].user_id == "admin-user"


def test_empty_profile_directory_returns_empty_tuple():
    repository = (
        SupabaseAdminTeacherDirectoryRepository(
            client=FakeClient(
                profiles=[],
            ),
        )
    )

    assert (
        repository.list_teachers()
        == ()
    )


def test_list_teachers_returns_normalized_read_model():
    client = FakeClient(
        profiles=[
            {
                "user_id": "teacher-1",
                "teacher_code": "  GV001  ",
                "full_name": "  Teacher One  ",
                "school_name": "  School A  ",
            },
        ],
    )

    repository = (
        SupabaseAdminTeacherDirectoryRepository(
            client=client,
        )
    )

    result = repository.list_teachers()

    assert len(result) == 1
    assert result[0].user_id == "teacher-1"
    assert result[0].teacher_code == "GV001"
    assert result[0].full_name == "Teacher One"
    assert result[0].school_name == "School A"


def test_list_teachers_sorts_by_name_then_teacher_code():
    client = FakeClient(
        profiles=[
            {
                "user_id": "teacher-1",
                "teacher_code": "GV002",
                "full_name": "Same Name",
                "school_name": "School A",
            },
            {
                "user_id": "teacher-2",
                "teacher_code": "GV001",
                "full_name": "Same Name",
                "school_name": "School A",
            },
        ],
    )

    repository = (
        SupabaseAdminTeacherDirectoryRepository(
            client=client,
        )
    )

    result = repository.list_teachers()

    assert tuple(
        item.teacher_code
        for item in result
    ) == (
        "GV001",
        "GV002",
    )
