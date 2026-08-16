from dataclasses import dataclass
from pathlib import Path

import pytest

from educational_planning_v2.adapters.supabase_teacher_subject_registration_repository import (
    SupabaseTeacherSubjectRegistrationRepository,
)
from educational_planning_v2.models.teacher_subject_registration import (
    TeacherSubjectRegistration,
    TeacherSubjectRegistrationStatus,
)


@dataclass
class Response:
    data: list


class FakeQuery:
    def __init__(
        self,
        client,
    ):
        self.client = client
        self.operation = None
        self.row = None
        self.filters = []
        self.orders = []
        self.limit_value = None

    def upsert(
        self,
        row,
        on_conflict,
    ):
        assert (
            on_conflict
            == "registration_id"
        )

        self.operation = "upsert"
        self.row = dict(row)
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

    def order(
        self,
        column,
    ):
        self.orders.append(
            column
        )
        return self

    def limit(
        self,
        value,
    ):
        self.limit_value = value
        return self

    def execute(self):
        if self.operation == "upsert":
            self.client.rows[
                self.row["registration_id"]
            ] = dict(self.row)

            return Response(
                [dict(self.row)]
            )

        result = list(
            self.client.rows.values()
        )

        for column, value in self.filters:
            result = [
                row
                for row in result
                if row.get(column)
                == value
            ]

        for column in reversed(
            self.orders
        ):
            result.sort(
                key=lambda row: (
                    row.get(column)
                    or ""
                )
            )

        if self.limit_value is not None:
            result = result[
                :self.limit_value
            ]

        if self.operation == "delete":
            ids = {
                row["registration_id"]
                for row in result
            }

            for registration_id in ids:
                self.client.rows.pop(
                    registration_id,
                    None,
                )

            return Response([])

        return Response(
            [
                dict(row)
                for row in result
            ]
        )


class FakeClient:
    def __init__(self):
        self.rows = {}

    def table(
        self,
        name,
    ):
        assert (
            name
            == "teacher_subject_registrations"
        )

        return FakeQuery(
            self
        )


def _registration(
    *,
    registration_id="registration-001",
    owner_id="user-1",
    subject_id="subject-math",
    component_id=None,
    status=(
        TeacherSubjectRegistrationStatus.ACTIVE
    ),
):
    return TeacherSubjectRegistration(
        registration_id=registration_id,
        owner_id=owner_id,
        academic_year="2026-2027",
        subject_id=subject_id,
        component_id=component_id,
        status=status,
    )


def test_save_get_list_find_and_delete():
    repository = (
        SupabaseTeacherSubjectRegistrationRepository(
            FakeClient(),
            "user-1",
        )
    )

    saved = repository.save(
        registration=_registration(
            component_id=(
                "component-math-algebra"
            )
        )
    )

    assert (
        saved.registration_id
        == "registration-001"
    )

    loaded = repository.get(
        registration_id="registration-001"
    )

    assert loaded is not None
    assert (
        loaded.component_id
        == "component-math-algebra"
    )

    listed = repository.list_registrations(
        owner_id="user-1",
        academic_year="2026-2027",
        status=(
            TeacherSubjectRegistrationStatus.ACTIVE
        ),
    )

    assert len(listed) == 1

    scope = repository.find_subject_scope(
        owner_id="user-1",
        academic_year="2026-2027",
        subject_id="subject-math",
        status=(
            TeacherSubjectRegistrationStatus.ACTIVE
        ),
    )

    assert len(scope) == 1

    repository.delete(
        registration_id="registration-001"
    )

    assert (
        repository.get(
            registration_id="registration-001"
        )
        is None
    )


def test_subject_level_registration_supported():
    repository = (
        SupabaseTeacherSubjectRegistrationRepository(
            FakeClient(),
            "user-1",
        )
    )

    saved = repository.save(
        registration=_registration(
            component_id=None
        )
    )

    assert saved.component_id is None


def test_subject_scope_filters_other_subjects():
    repository = (
        SupabaseTeacherSubjectRegistrationRepository(
            FakeClient(),
            "user-1",
        )
    )

    repository.save(
        registration=_registration(
            registration_id="math-1",
            subject_id="subject-math",
        )
    )

    repository.save(
        registration=_registration(
            registration_id="art-1",
            subject_id="subject-art",
        )
    )

    scope = repository.find_subject_scope(
        owner_id="user-1",
        academic_year="2026-2027",
        subject_id="subject-math",
    )

    assert len(scope) == 1
    assert (
        scope[0].subject_id
        == "subject-math"
    )


def test_status_filter_supported():
    repository = (
        SupabaseTeacherSubjectRegistrationRepository(
            FakeClient(),
            "user-1",
        )
    )

    repository.save(
        registration=_registration(
            registration_id="active-1",
            status=(
                TeacherSubjectRegistrationStatus.ACTIVE
            ),
        )
    )

    repository.save(
        registration=_registration(
            registration_id="inactive-1",
            status=(
                TeacherSubjectRegistrationStatus.INACTIVE
            ),
        )
    )

    active = repository.list_registrations(
        owner_id="user-1",
        academic_year="2026-2027",
        status=(
            TeacherSubjectRegistrationStatus.ACTIVE
        ),
    )

    assert len(active) == 1
    assert (
        active[0].registration_id
        == "active-1"
    )


def test_cross_owner_save_blocked():
    repository = (
        SupabaseTeacherSubjectRegistrationRepository(
            FakeClient(),
            "user-1",
        )
    )

    with pytest.raises(
        ValueError,
        match="owner_id",
    ):
        repository.save(
            registration=_registration(
                owner_id="user-2"
            )
        )


def test_cross_owner_list_blocked():
    repository = (
        SupabaseTeacherSubjectRegistrationRepository(
            FakeClient(),
            "user-1",
        )
    )

    with pytest.raises(
        ValueError,
        match="owner_id",
    ):
        repository.list_registrations(
            owner_id="user-2",
            academic_year="2026-2027",
        )


def test_cross_owner_subject_scope_blocked():
    repository = (
        SupabaseTeacherSubjectRegistrationRepository(
            FakeClient(),
            "user-1",
        )
    )

    with pytest.raises(
        ValueError,
        match="owner_id",
    ):
        repository.find_subject_scope(
            owner_id="user-2",
            academic_year="2026-2027",
            subject_id="subject-math",
        )


def test_invalid_status_filter_blocked():
    repository = (
        SupabaseTeacherSubjectRegistrationRepository(
            FakeClient(),
            "user-1",
        )
    )

    with pytest.raises(TypeError):
        repository.list_registrations(
            owner_id="user-1",
            academic_year="2026-2027",
            status="ACTIVE",
        )


def test_registration_type_required():
    repository = (
        SupabaseTeacherSubjectRegistrationRepository(
            FakeClient(),
            "user-1",
        )
    )

    with pytest.raises(TypeError):
        repository.save(
            registration="subject-math"
        )


def test_repository_requires_client():
    with pytest.raises(ValueError):
        SupabaseTeacherSubjectRegistrationRepository(
            None,
            "user-1",
        )


def test_migration_contains_rls_and_foreign_keys():
    root = Path(
        __file__
    ).resolve().parents[3]

    sql = (
        root
        / "supabase"
        / "migrations"
        / "202608160007_teacher_subject_registrations.sql"
    ).read_text(
        encoding="utf-8"
    ).lower()

    assert (
        "references public.subjects"
        in sql
    )

    assert (
        "references public.subject_components"
        in sql
    )

    assert (
        "enable row level security"
        in sql
    )

    assert "auth.uid()" in sql
    assert "owner_id" in sql
