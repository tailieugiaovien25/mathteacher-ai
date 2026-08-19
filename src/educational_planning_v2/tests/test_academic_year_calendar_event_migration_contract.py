from pathlib import Path


MIGRATION_PATH = Path(
    "supabase/migrations/"
    "202608180006_academic_year_calendar_events.sql"
)


def _sql() -> str:
    return MIGRATION_PATH.read_text(
        encoding="utf-8"
    ).lower()


def test_calendar_event_table_exists():
    sql = _sql()

    assert (
        "public.academic_year_calendar_events"
        in sql
    )


def test_calendar_event_references_academic_year():
    sql = _sql()

    assert (
        "public.academic_year_configurations"
        in sql
    )

    assert (
        "academic_year_id"
        in sql
    )


def test_calendar_event_types_are_canonical():
    sql = _sql()

    expected = (
        "'holiday'",
        "'tet_break'",
        "'midterm_break'",
        "'makeup_day'",
        "'school_event'",
        "'other_break'",
    )

    for value in expected:
        assert value in sql


def test_makeup_day_requires_teaching_override():
    sql = _sql()

    assert (
        "event_type = 'makeup_day'"
        in sql
    )

    assert (
        "is_teaching_day_override = true"
        in sql
    )


def test_non_makeup_events_cannot_override_teaching_day():
    sql = _sql()

    assert (
        "event_type <> 'makeup_day'"
        in sql
    )

    assert (
        "is_teaching_day_override = false"
        in sql
    )


def test_event_date_order_is_enforced():
    sql = _sql()

    assert (
        "start_date <= end_date"
        in sql
    )


def test_authenticated_users_can_read():
    sql = _sql()

    assert (
        '"authenticated_select_academic_year_calendar_events"'
        in sql
    )

    assert "for select" in sql
    assert "to authenticated" in sql


def test_only_admin_can_write():
    sql = _sql()

    policies = (
        '"admins_insert_academic_year_calendar_events"',
        '"admins_update_academic_year_calendar_events"',
        '"admins_delete_academic_year_calendar_events"',
    )

    for policy in policies:
        assert policy in sql

    assert (
        "current_user_is_portal_admin()"
        in sql
    )


def test_calendar_event_indexes_exist():
    sql = _sql()

    assert (
        "academic_year_calendar_events_year_date_idx"
        in sql
    )

    assert (
        "academic_year_calendar_events_year_type_idx"
        in sql
    )
