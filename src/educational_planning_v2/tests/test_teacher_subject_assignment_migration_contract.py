from pathlib import Path


MIGRATION_PATH = Path(
    "supabase/migrations/"
    "202608180004_teacher_subject_assignments.sql"
)


def _sql() -> str:
    return MIGRATION_PATH.read_text(
        encoding="utf-8"
    ).lower()


def test_teacher_subject_assignment_table_exists():
    sql = _sql()

    assert (
        "create table if not exists"
        in sql
    )

    assert (
        "public.teacher_subject_assignments"
        in sql
    )


def test_subject_assignment_references_canonical_subject():
    sql = _sql()

    assert (
        "references public.subjects(subject_id)"
        in sql
    )


def test_subject_assignment_references_teacher_identity():
    sql = _sql()

    assert (
        "references auth.users(id)"
        in sql
    )


def test_subject_assignment_scope_is_unique():
    sql = _sql()

    assert (
        "teacher_subject_assignments_scope_unique"
        in sql
    )

    assert (
        "teacher_id,"
        in sql
    )

    assert (
        "academic_year,"
        in sql
    )

    assert (
        "subject_id"
        in sql
    )


def test_subject_assignment_contains_no_class_scope():
    sql = _sql()

    forbidden_column_patterns = (
        "class_id text",
        "class_id uuid",
        "class_id varchar",
    )

    for pattern in forbidden_column_patterns:
        assert pattern not in sql


def test_subject_assignment_contains_no_component_scope():
    sql = _sql()

    forbidden_column_patterns = (
        "component_id text",
        "component_id uuid",
        "component_id varchar",
    )

    for pattern in forbidden_column_patterns:
        assert pattern not in sql


def test_teacher_can_only_select_own_assignments():
    sql = _sql()

    assert (
        '"teachers_select_own_subject_assignments"'
        in sql
    )

    assert (
        "(select auth.uid()) = teacher_id"
        in sql
    )


def test_teacher_has_no_subject_assignment_mutation_policy():
    sql = _sql()

    forbidden = (
        "teachers_insert_own_subject_assignments",
        "teachers_update_own_subject_assignments",
        "teachers_delete_own_subject_assignments",
    )

    for token in forbidden:
        assert token not in sql


def test_admin_can_manage_subject_assignments():
    sql = _sql()

    policies = (
        '"admins_select_teacher_subject_assignments"',
        '"admins_insert_teacher_subject_assignments"',
        '"admins_update_teacher_subject_assignments"',
        '"admins_delete_teacher_subject_assignments"',
    )

    for policy in policies:
        assert policy in sql

    assert (
        "current_user_is_portal_admin()"
        in sql
    )


def test_status_is_lifecycle_based():
    sql = _sql()

    assert "'active'" in sql
    assert "'inactive'" in sql
