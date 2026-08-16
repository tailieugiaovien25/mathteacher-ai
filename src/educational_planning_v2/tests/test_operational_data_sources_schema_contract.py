from __future__ import annotations

from pathlib import Path

from educational_planning_v2.models.operational_data_source import (
    OperationalDataOrigin,
    OperationalDataStatus,
    OperationalDataType,
)


MIGRATION_PATH = Path(
    "supabase/migrations/"
    "20260816_create_operational_data_sources.sql"
)


def run_contract() -> bool:
    print("=" * 72)
    print(
        "MVP-OPS-003B.5B.3 - "
        "OPERATIONAL DATA SOURCES SCHEMA & RLS CONTRACT TEST"
    )
    print("=" * 72)

    sql = MIGRATION_PATH.read_text(
        encoding="utf-8"
    )

    lower = sql.lower()

    tests = []

    tests.append((
        "ODSDB1 Migration exists",
        MIGRATION_PATH.exists(),
    ))

    tests.append((
        "ODSDB2 Operational table declared",
        (
            "create table if not exists "
            "public.operational_data_sources"
        )
        in lower,
    ))

    tests.append((
        "ODSDB3 User identity column exists",
        "user_id uuid not null"
        in lower,
    ))

    tests.append((
        "ODSDB4 Source identity column exists",
        "source_id text not null"
        in lower,
    ))

    tests.append((
        "ODSDB5 Composite primary key locked",
        (
            "primary key"
            in lower
            and
            "user_id"
            in lower
            and
            "source_id"
            in lower
        ),
    ))

    tests.append((
        "ODSDB6 Owner must match authenticated user identity",
        "owner_id = user_id::text"
        in lower,
    ))

    tests.append((
        "ODSDB7 Workspace lookup index exists",
        (
            "idx_operational_data_sources_workspace"
            in lower
            and
            "academic_year"
            in lower
            and
            "data_type"
            in lower
            and
            "status"
            in lower
        ),
    ))

    tests.append((
        "ODSDB8 RLS enabled",
        (
            "alter table public.operational_data_sources"
            in lower
            and
            "enable row level security"
            in lower
        ),
    ))

    tests.append((
        "ODSDB9 SELECT own-row policy exists",
        (
            "operational_data_sources_select_own"
            in lower
            and
            "for select"
            in lower
            and
            "auth.uid() = user_id"
            in lower
        ),
    ))

    tests.append((
        "ODSDB10 INSERT own-row policy exists",
        (
            "operational_data_sources_insert_own"
            in lower
            and
            "for insert"
            in lower
            and
            "owner_id = auth.uid()::text"
            in lower
        ),
    ))

    tests.append((
        "ODSDB11 UPDATE own-row policy exists",
        (
            "operational_data_sources_update_own"
            in lower
            and
            "for update"
            in lower
            and
            "auth.uid() = user_id"
            in lower
        ),
    ))

    tests.append((
        "ODSDB12 DELETE own-row policy exists",
        (
            "operational_data_sources_delete_own"
            in lower
            and
            "for delete"
            in lower
            and
            "auth.uid() = user_id"
            in lower
        ),
    ))

    for data_type in OperationalDataType:
        tests.append((
            f"ODSDB-DT-{data_type.name} data type allowed",
            f"'{data_type.value}'"
            in sql,
        ))

    for origin in OperationalDataOrigin:
        tests.append((
            f"ODSDB-ORIGIN-{origin.name} origin allowed",
            f"'{origin.value}'"
            in sql,
        ))

    for status in OperationalDataStatus:
        tests.append((
            f"ODSDB-STATUS-{status.name} status allowed",
            f"'{status.value}'"
            in sql,
        ))

    tests.append((
        "ODSDB13 Schema stores metadata only",
        not any(
            token
            in lower
            for token in (
                "payload",
                "workbook_bytes",
                "document_bytes",
                "schedule_data",
            )
        ),
    ))

    tests.append((
        "ODSDB14 No fixed educational values",
        not any(
            token
            in sql
            for token in (
                "140",
                "105",
                "70",
                "35",
                "KNTT",
                "To?n 6",
            )
        ),
    ))

    results = []

    for label, passed in tests:
        results.append(passed)
        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print()

    if all(results):
        print(
            "RESULT: PASS - OPERATIONAL DATA SOURCES "
            "SCHEMA & RLS CONTRACT VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - OPERATIONAL DATA SOURCES "
        "SCHEMA & RLS CONTRACT VIOLATED"
    )

    return False


def test_operational_data_sources_schema_contract():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
