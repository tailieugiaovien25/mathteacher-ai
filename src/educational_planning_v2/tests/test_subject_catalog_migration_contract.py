from pathlib import Path


def _migration_sql() -> str:
    root = Path(
        __file__
    ).resolve().parents[3]

    path = (
        root
        / "supabase"
        / "migrations"
        / "202608160005_subject_catalog.sql"
    )

    assert path.exists(), (
        "subject catalog migration is missing"
    )

    return path.read_text(
        encoding="utf-8"
    ).lower()


def test_subjects_table_exists():
    sql = _migration_sql()

    assert (
        "create table if not exists public.subjects"
        in sql
    )


def test_subject_components_table_exists():
    sql = _migration_sql()

    assert (
        "public.subject_components"
        in sql
    )


def test_component_policy_contract_is_preserved():
    sql = _migration_sql()

    assert "component_policy" in sql

    for value in (
        "'none'",
        "'optional'",
        "'required'",
    ):
        assert value in sql


def test_component_belongs_to_subject():
    sql = _migration_sql()

    assert (
        "references public.subjects"
        in sql
    )

    assert (
        "subject_id"
        in sql
    )


def test_subject_catalog_has_active_inactive_status():
    sql = _migration_sql()

    assert "'active'" in sql
    assert "'inactive'" in sql


def test_subjects_rls_is_enabled():
    sql = _migration_sql()

    assert (
        "alter table\n"
        "    public.subjects\n"
        "enable row level security"
        in sql
    )


def test_subject_components_rls_is_enabled():
    sql = _migration_sql()

    assert (
        "alter table\n"
        "    public.subject_components\n"
        "enable row level security"
        in sql
    )


def test_anonymous_role_has_no_catalog_access():
    sql = _migration_sql()

    assert (
        "revoke all\n"
        "on table public.subjects\n"
        "from anon"
        in sql
    )

    assert (
        "revoke all\n"
        "on table public.subject_components\n"
        "from anon"
        in sql
    )


def test_authenticated_users_can_read_subjects():
    sql = _migration_sql()

    assert (
        "grant select\n"
        "on table public.subjects\n"
        "to authenticated"
        in sql
    )

    assert (
        '"authenticated_read_subjects"'
        in sql
    )


def test_authenticated_users_can_read_components():
    sql = _migration_sql()

    assert (
        "grant select\n"
        "on table public.subject_components\n"
        "to authenticated"
        in sql
    )

    assert (
        '"authenticated_read_subject_components"'
        in sql
    )


def test_subject_write_policies_require_admin():
    sql = _migration_sql()

    policies = (
        '"admin_insert_subjects"',
        '"admin_update_subjects"',
        '"admin_delete_subjects"',
    )

    for policy in policies:
        assert policy in sql

    assert "public.portal_roles" in sql
    assert "pr.role = 'admin'" in sql


def test_component_write_policies_require_admin():
    sql = _migration_sql()

    policies = (
        '"admin_insert_subject_components"',
        '"admin_update_subject_components"',
        '"admin_delete_subject_components"',
    )

    for policy in policies:
        assert policy in sql

    assert "public.portal_roles" in sql
    assert "pr.role = 'admin'" in sql


def test_subject_code_is_unique():
    sql = _migration_sql()

    assert (
        "code text not null unique"
        in sql
    )


def test_component_code_unique_inside_subject():
    sql = _migration_sql()

    assert (
        "subject_components_subject_code_unique"
        in sql
    )

    assert (
        "unique (\n"
        "            subject_id,\n"
        "            code\n"
        "        )"
        in sql
    )


def test_component_delete_follows_subject_delete():
    sql = _migration_sql()

    assert "on delete cascade" in sql


def test_catalog_supports_stable_display_order():
    sql = _migration_sql()

    assert sql.count(
        "display_order integer not null"
    ) >= 2

    assert sql.count(
        "display_order >= 0"
    ) >= 2
