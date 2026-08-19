from pathlib import Path


MIGRATION_PATH = Path(
    "supabase/migrations/"
    "202608180007_admin_teaching_assignments.sql"
)


def _sql() -> str:
    return MIGRATION_PATH.read_text(
        encoding="utf-8"
    ).lower()


def test_teacher_select_policy_is_preserved():
    sql = _sql()

    assert (
        "teachers_select_own_assignments"
        not in sql
        or (
            "drop policy if exists"
            not in sql.split(
                "teachers_select_own_assignments"
            )[0][-80:]
        )
    )


def test_teacher_write_policies_are_removed():
    sql = _sql()

    expected = (
        '"teachers_insert_own_assignments"',
        '"teachers_update_own_assignments"',
        '"teachers_delete_own_assignments"',
    )

    for policy in expected:
        assert policy in sql
        assert "drop policy if exists" in sql


def test_admin_select_policy_exists():
    sql = _sql()

    assert (
        '"admins_select_teaching_assignments"'
        in sql
    )
    assert "for select" in sql


def test_admin_write_policies_exist():
    sql = _sql()

    expected = (
        '"admins_insert_teaching_assignments"',
        '"admins_update_teaching_assignments"',
        '"admins_delete_teaching_assignments"',
    )

    for policy in expected:
        assert policy in sql


def test_admin_authorization_uses_canonical_helper():
    sql = _sql()

    assert (
        "public.current_user_is_portal_admin()"
        in sql
    )


def test_migration_does_not_disable_rls():
    sql = _sql()

    assert (
        "disable row level security"
        not in sql
    )


def test_migration_targets_teaching_assignments():
    sql = _sql()

    assert (
        "public.teaching_assignments"
        in sql
    )
