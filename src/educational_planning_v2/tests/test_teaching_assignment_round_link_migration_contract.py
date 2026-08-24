from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608190002_teaching_assignment_round_link.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(
        encoding="utf-8"
    )


def test_migration_exists():
    assert MIGRATION.exists()


def test_assignment_round_column_added():
    sql = _sql()

    assert (
        "add column if not exists\n"
        "    assignment_round_id text null;"
        in sql
    )


def test_assignment_round_foreign_key_created():
    sql = _sql()

    assert (
        "teaching_assignments_assignment_round_fk"
        in sql
    )

    assert (
        "references public.assignment_rounds (\n"
        "    round_id\n"
        ")"
        in sql
    )


def test_assignment_round_foreign_key_restricts_delete():
    sql = _sql()

    assert "on delete restrict;" in sql


def test_assignment_round_foreign_key_cascades_update():
    sql = _sql()

    assert "on update cascade" in sql


def test_assignment_round_index_created():
    sql = _sql()

    assert (
        "teaching_assignments_round_idx"
        in sql
    )


def test_year_round_index_created():
    sql = _sql()

    assert (
        "teaching_assignments_year_round_idx"
        in sql
    )

    assert (
        "academic_year,\n"
        "    assignment_round_id"
        in sql
    )


def test_assignment_round_column_remains_nullable():
    sql = _sql()

    assert (
        "assignment_round_id text null"
        in sql
    )


def test_assignment_round_column_documented():
    sql = _sql()

    assert (
        "comment on column\n"
        "public.teaching_assignments."
        "assignment_round_id is"
        in sql
    )
