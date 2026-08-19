from pathlib import Path


MIGRATION_PATH = Path(
    "supabase/migrations/"
    "202608180003_admin_portal_roles_read.sql"
)


def _sql() -> str:
    return MIGRATION_PATH.read_text(
        encoding="utf-8"
    ).lower()


def test_admin_portal_roles_policy_exists():
    sql = _sql()

    assert (
        '"admins_select_portal_roles"'
        in sql
    )


def test_admin_portal_roles_policy_is_select_only():
    sql = _sql()

    assert "for select" in sql


def test_admin_portal_roles_policy_uses_admin_helper():
    sql = _sql()

    assert (
        "current_user_is_portal_admin()"
        in sql
    )


def test_migration_does_not_grant_role_mutation():
    sql = _sql()

    forbidden = (
        "for insert",
        "for update",
        "for delete",
        "grant insert",
        "grant update",
        "grant delete",
    )

    for token in forbidden:
        assert token not in sql
