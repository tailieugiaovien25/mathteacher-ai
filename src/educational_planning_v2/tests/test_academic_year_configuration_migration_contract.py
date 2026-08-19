from pathlib import Path


MIGRATION_PATH = Path(
    "supabase/migrations/"
    "202608180005_academic_year_configurations.sql"
)


def _sql() -> str:
    return MIGRATION_PATH.read_text(
        encoding="utf-8"
    ).lower()


def test_academic_year_table_exists():
    sql = _sql()

    assert (
        "public.academic_year_configurations"
        in sql
    )


def test_academic_year_uses_canonical_format():
    sql = _sql()

    assert (
        "'^[0-9]{4}-[0-9]{4}$'"
        in sql
    )


def test_only_one_current_academic_year_is_allowed():
    sql = _sql()

    assert (
        "academic_year_configurations_one_current_idx"
        in sql
    )

    assert (
        "where is_current = true"
        in sql
    )


def test_current_academic_year_must_be_active():
    sql = _sql()

    assert (
        "academic_year_current_active_check"
        in sql
    )

    assert (
        "not is_current"
        in sql
    )

    assert (
        "status = 'active'"
        in sql
    )


def test_authenticated_users_can_read():
    sql = _sql()

    assert (
        '"authenticated_select_academic_year_configurations"'
        in sql
    )

    assert "for select" in sql
    assert "to authenticated" in sql


def test_only_admin_can_write():
    sql = _sql()

    policies = (
        '"admins_insert_academic_year_configurations"',
        '"admins_update_academic_year_configurations"',
        '"admins_delete_academic_year_configurations"',
    )

    for policy in policies:
        assert policy in sql

    assert (
        "current_user_is_portal_admin()"
        in sql
    )


def test_school_year_calendar_fields_exist():
    sql = _sql()

    required_fields = (
        "start_date",
        "end_date",
        "opening_ceremony_date",
        "semester_1_start",
        "semester_1_end",
        "semester_2_start",
        "semester_2_end",
    )

    for field_name in required_fields:
        assert field_name in sql
