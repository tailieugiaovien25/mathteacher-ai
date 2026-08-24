from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608190004_class_catalogs.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(
        encoding="utf-8"
    )


def test_class_catalog_migration_exists():
    assert MIGRATION.exists()


def test_class_catalog_table_created():
    sql = _sql()

    assert (
        "create table if not exists "
        "public.class_catalogs"
        in sql
    )


def test_class_catalog_has_flexible_fields():
    sql = _sql()

    assert "grade_level text not null" in sql
    assert "class_code text not null" in sql
    assert "class_name text not null" in sql


def test_class_catalog_year_code_unique():
    sql = _sql()

    assert (
        "class_catalog_year_code_unique"
        in sql
    )

    assert (
        "academic_year,\n"
        "            class_code"
        in sql
    )


def test_class_catalog_does_not_limit_class_count():
    sql = _sql()

    assert "class_count" not in sql
    assert "max_classes" not in sql


def test_class_catalog_status_contract():
    sql = _sql()

    assert "'ACTIVE'" in sql
    assert "'INACTIVE'" in sql


def test_class_catalog_rls_enabled():
    sql = _sql()

    assert (
        "alter table\n"
        "    public.class_catalogs\n"
        "enable row level security;"
        in sql
    )


def test_authenticated_users_can_read():
    sql = _sql()

    assert (
        '"authenticated_select_class_catalogs"'
        in sql
    )

    assert (
        "(select auth.uid()) is not null"
        in sql
    )


def test_admin_can_insert():
    sql = _sql()

    assert (
        '"admins_insert_class_catalogs"'
        in sql
    )

    assert (
        "public.current_user_is_portal_admin()"
        in sql
    )


def test_admin_update_has_using_and_with_check():
    sql = _sql()

    block_start = sql.index(
        '"admins_update_class_catalogs"'
    )

    block_end = sql.index(
        '"admins_delete_class_catalogs"',
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


def test_admin_can_delete():
    sql = _sql()

    block_start = sql.index(
        '"admins_delete_class_catalogs"'
    )

    block = sql[
        block_start:
    ]

    assert "for delete" in block
    assert "using (" in block
    assert (
        "public.current_user_is_portal_admin()"
        in block
    )


def test_class_catalog_has_year_grade_index():
    sql = _sql()

    assert (
        "class_catalogs_year_grade_idx"
        in sql
    )


def test_class_catalog_is_documented_as_data_driven():
    sql = _sql()

    assert (
        "Class count and names are data-driven "
        "and not hard-coded."
        in sql
    )
