from pathlib import Path


def _root() -> Path:
    return Path(
        __file__
    ).resolve().parents[3]


def _notification_sql() -> str:
    return (
        _root()
        / "supabase"
        / "migrations"
        / "202608170001_notifications.sql"
    ).read_text(
        encoding="utf-8-sig"
    ).lower()


def test_notifications_table_exists():
    sql = _notification_sql()

    assert (
        "public.notifications"
        in sql
    )

    assert (
        "notification_id text primary key"
        in sql
    )


def test_notification_owner_is_required():
    sql = _notification_sql()

    assert "owner_id uuid not null" in sql
    assert "references auth.users(id)" in sql
    assert "on delete cascade" in sql


def test_notification_generic_types_are_constrained():
    sql = _notification_sql()

    for value in (
        "data_changed",
        "assignment_changed",
        "schedule_changed",
        "process_completed",
        "system",
    ):
        assert value in sql


def test_notification_priority_is_constrained():
    sql = _notification_sql()

    for value in (
        "low",
        "normal",
        "high",
        "urgent",
    ):
        assert value in sql


def test_notification_status_is_constrained():
    sql = _notification_sql()

    for value in (
        "unread",
        "read",
        "archived",
    ):
        assert value in sql


def test_notification_read_state_is_consistent():
    sql = _notification_sql()

    assert (
        "notification_read_state_consistency"
        in sql
    )

    assert "status = 'unread'" in sql
    assert "read_at is null" in sql
    assert "status = 'read'" in sql
    assert "read_at is not null" in sql


def test_notification_owner_status_index_exists():
    sql = _notification_sql()

    assert (
        "notifications_owner_status_created_idx"
        in sql
    )

    assert "owner_id" in sql
    assert "status" in sql
    assert "created_at desc" in sql


def test_notification_rls_is_enabled():
    sql = _notification_sql()

    assert (
        "enable row level security"
        in sql
    )

    assert "auth.uid()" in sql
    assert "owner_id" in sql


def test_notification_anon_access_is_revoked():
    sql = _notification_sql()

    assert "revoke all" in sql
    assert "from anon" in sql


def test_notification_owner_policies_exist():
    sql = _notification_sql()

    for policy in (
        "users_select_own_notifications",
        "users_insert_own_notifications",
        "users_update_own_notifications",
        "users_delete_own_notifications",
    ):
        assert policy in sql


def test_notification_has_no_service_role_policy():
    sql = _notification_sql()

    assert "service_role" not in sql


def test_notification_update_policy_is_explicit():
    sql = _notification_sql()

    start = sql.find(
        'create policy\n'
        '    "users_update_own_notifications"'
    )

    assert start != -1

    end = sql.find(
        "with check",
        start,
    )

    assert end != -1

    policy = sql[start:end]

    assert "for update" in policy
    assert "to authenticated" in policy
    assert "auth.uid()" in policy
    assert "owner_id" in policy
