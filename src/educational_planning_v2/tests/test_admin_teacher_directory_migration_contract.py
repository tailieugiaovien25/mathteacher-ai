from pathlib import Path


MIGRATION_PATH = Path(
    "supabase/migrations/"
    "202608180002_admin_teacher_directory_read.sql"
)


def _sql() -> str:
    return MIGRATION_PATH.read_text(
        encoding="utf-8"
    ).lower()


def test_admin_helper_exists():
    sql = _sql()

    assert (
        "create or replace function "
        "public.current_user_is_portal_admin()"
        in sql
    )


def test_admin_helper_uses_canonical_role():
    sql = _sql()

    assert "pr.role = 'admin'" in sql
    assert "pr.role = 'ADMIN'" not in sql


def test_admin_helper_is_security_definer():
    sql = _sql()

    assert "security definer" in sql
    assert "set search_path = ''" in sql


def test_admin_teacher_profile_policy_is_select_only():
    sql = _sql()

    assert (
        '"admins_select_teacher_profiles"'
        in sql
    )

    assert "for select" in sql

    assert (
        "current_user_is_portal_admin()"
        in sql
    )


def test_migration_does_not_add_admin_profile_mutation_policy():
    sql = _sql()

    forbidden = (
        "admins_insert_teacher_profiles",
        "admins_update_teacher_profiles",
        "admins_delete_teacher_profiles",
    )

    for token in forbidden:
        assert token not in sql
