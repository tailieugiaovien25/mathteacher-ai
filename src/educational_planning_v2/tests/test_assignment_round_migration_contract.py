from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608190001_assignment_rounds.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(
        encoding="utf-8"
    )


def test_assignment_round_migration_exists():
    assert MIGRATION.exists()


def test_assignment_round_table_created():
    sql = _sql()

    assert (
        "create table if not exists "
        "public.assignment_rounds"
        in sql
    )


def test_assignment_round_year_number_is_unique():
    sql = _sql()

    assert (
        "assignment_round_year_number_unique"
        in sql
    )

    assert (
        "academic_year,\n"
        "            round_number"
        in sql
    )


def test_assignment_round_number_must_be_positive():
    sql = _sql()

    assert "round_number >= 1" in sql


def test_assignment_round_status_contract():
    sql = _sql()

    assert "'ACTIVE'" in sql
    assert "'CLOSED'" in sql


def test_assignment_round_rls_enabled():
    sql = _sql()

    assert (
        "alter table\n"
        "    public.assignment_rounds\n"
        "enable row level security;"
        in sql
    )


def test_authenticated_users_can_read_rounds():
    sql = _sql()

    assert (
        '"authenticated_select_assignment_rounds"'
        in sql
    )

    assert (
        "(select auth.uid()) is not null"
        in sql
    )


def test_only_admin_can_insert_rounds():
    sql = _sql()

    assert (
        '"admins_insert_assignment_rounds"'
        in sql
    )

    assert (
        "with check (\n"
        "    (select "
        "public.current_user_is_portal_admin())\n"
        ");"
        in sql
    )


def test_admin_update_policy_has_using_and_with_check():
    sql = _sql()

    block_start = sql.index(
        '"admins_update_assignment_rounds"'
    )

    block_end = sql.index(
        '"admins_delete_assignment_rounds"',
        block_start,
    )

    block = sql[
        block_start:block_end
    ]

    assert "for update" in block
    assert "using (" in block
    assert "with check (" in block

    assert (
        block.count(
            "public.current_user_is_portal_admin()"
        )
        >= 2
    )


def test_only_admin_can_delete_rounds():
    sql = _sql()

    block_start = sql.index(
        '"admins_delete_assignment_rounds"'
    )

    block = sql[
        block_start:
    ]

    assert "for delete" in block
    assert (
        "public.current_user_is_portal_admin()"
        in block
    )
