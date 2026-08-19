from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608190003_assignment_round_backfill.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(
        encoding="utf-8"
    )


def test_backfill_migration_exists():
    assert MIGRATION.exists()


def test_backfill_uses_current_active_academic_year():
    sql = _sql()

    assert (
        "from public.academic_year_configurations"
        in sql
    )
    assert "where is_current = true" in sql
    assert "status = 'ACTIVE'" in sql


def test_backfill_uses_academic_year_start_date():
    sql = _sql()

    assert "start_date" in sql
    assert "current_start_date" in sql


def test_backfill_targets_round_one():
    sql = _sql()

    assert "round_number = 1" in sql
    assert "'L\u1ea7n 1'" in sql


def test_backfill_creates_round_only_if_missing():
    sql = _sql()

    assert "if first_round_id is null then" in sql

    assert (
        "on conflict (\n"
        "            academic_year,\n"
        "            round_number\n"
        "        )\n"
        "        do nothing;"
        in sql
    )


def test_backfill_updates_only_unassigned_records():
    sql = _sql()

    assert (
        "assignment_round_id is null"
        in sql
    )


def test_backfill_stays_inside_current_academic_year():
    sql = _sql()

    assert (
        "where academic_year = current_year"
        in sql
    )


def test_backfill_sets_round_id_and_updated_at():
    sql = _sql()

    assert (
        "assignment_round_id = first_round_id"
        in sql
    )

    assert "updated_at = now()" in sql


def test_backfill_skips_safely_without_current_year():
    sql = _sql()

    assert "if current_year is null then" in sql

    assert (
        "assignment round backfill skipped."
        in sql
    )


def test_backfill_is_idempotent():
    sql = _sql()

    assert (
        "on conflict (\n"
        "            academic_year,\n"
        "            round_number\n"
        "        )\n"
        "        do nothing;"
        in sql
    )

    assert (
        "assignment_round_id is null"
        in sql
    )
