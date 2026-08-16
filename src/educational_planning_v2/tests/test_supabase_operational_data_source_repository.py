from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.adapters.supabase_operational_data_source_repository import (
    SupabaseOperationalDataSourceRepository,
)
from educational_planning_v2.models.operational_data_source import (
    OperationalDataOrigin,
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)


@dataclass
class FakeResponse:
    data: list[dict]


class FakeQuery:
    def __init__(
        self,
        table,
        operation: str = "select",
    ) -> None:
        self._table = table
        self._operation = operation
        self._filters: list[tuple[str, object]] = []
        self._limit = None
        self._order_column = None
        self._upsert_row = None

    def select(self, columns: str):
        self._operation = "select"
        return self

    def upsert(
        self,
        row: dict,
        on_conflict: str,
    ):
        self._operation = "upsert"
        self._upsert_row = dict(row)
        self._on_conflict = on_conflict
        return self

    def delete(self):
        self._operation = "delete"
        return self

    def eq(
        self,
        field: str,
        value,
    ):
        self._filters.append(
            (field, value)
        )
        return self

    def limit(self, value: int):
        self._limit = value
        return self

    def order(
        self,
        column: str,
        desc: bool = False,
    ):
        self._order_column = column
        self._order_desc = desc
        return self

    def execute(self):
        if self._operation == "upsert":
            return self._execute_upsert()

        if self._operation == "delete":
            return self._execute_delete()

        return self._execute_select()

    def _matches(
        self,
        row: dict,
    ) -> bool:
        return all(
            row.get(field) == value
            for field, value
            in self._filters
        )

    def _execute_select(self):
        rows = [
            dict(row)
            for row in self._table.rows
            if self._matches(row)
        ]

        if self._order_column is not None:
            rows.sort(
                key=lambda row: row.get(
                    self._order_column
                ),
                reverse=getattr(
                    self,
                    "_order_desc",
                    False,
                ),
            )

        if self._limit is not None:
            rows = rows[
                : self._limit
            ]

        return FakeResponse(
            data=rows
        )

    def _execute_upsert(self):
        row = dict(
            self._upsert_row
        )

        identity = (
            row["user_id"],
            row["source_id"],
        )

        existing_index = None

        for index, existing in enumerate(
            self._table.rows
        ):
            if (
                existing["user_id"],
                existing["source_id"],
            ) == identity:
                existing_index = index
                break

        if existing_index is None:
            self._table.rows.append(
                row
            )
        else:
            self._table.rows[
                existing_index
            ] = row

        return FakeResponse(
            data=[dict(row)]
        )

    def _execute_delete(self):
        deleted = []

        kept = []

        for row in self._table.rows:
            if self._matches(row):
                deleted.append(
                    dict(row)
                )
            else:
                kept.append(row)

        self._table.rows = kept

        return FakeResponse(
            data=deleted
        )


class FakeTable:
    def __init__(
        self,
        rows: list[dict],
    ) -> None:
        self.rows = rows

    def select(
        self,
        columns: str,
    ):
        return FakeQuery(
            self
        ).select(columns)

    def upsert(
        self,
        row: dict,
        on_conflict: str,
    ):
        return FakeQuery(
            self
        ).upsert(
            row,
            on_conflict,
        )

    def delete(self):
        return FakeQuery(
            self
        ).delete()


class FakeSupabaseClient:
    def __init__(self) -> None:
        self.tables = {
            "operational_data_sources":
                FakeTable([])
        }

    def table(
        self,
        table_name: str,
    ) -> FakeTable:
        return self.tables[
            table_name
        ]


def make_source(
    *,
    source_id: str,
    owner_id: str = "teacher-001",
    academic_year: str = "2026-2027",
    data_type: OperationalDataType = OperationalDataType.PPCT,
    status: OperationalDataStatus = OperationalDataStatus.ACTIVE,
) -> OperationalDataSource:
    return OperationalDataSource(
        source_id=source_id,
        data_type=data_type,
        origin=OperationalDataOrigin.FILE_IMPORTED,
        owner_id=owner_id,
        academic_year=academic_year,
        status=status,
        source_name=source_id,
        source_version="1",
    )


def expect_error(
    error_type,
    action,
) -> bool:
    try:
        action()
    except error_type:
        return True
    except Exception:
        return False

    return False


def run_contract() -> bool:
    print("=" * 72)
    print(
        "MVP-OPS-003B.5B.2 - "
        "SUPABASE OPERATIONAL DATA SOURCE REPOSITORY TEST"
    )
    print("=" * 72)

    client = FakeSupabaseClient()

    repository = (
        SupabaseOperationalDataSourceRepository(
            client=client,
            user_id="teacher-001",
        )
    )

    tests = []

    ppct = make_source(
        source_id="ppct-001"
    )

    saved = repository.save(
        source=ppct
    )

    tests.append((
        "SODR1 Repository user normalized",
        repository.user_id
        == "teacher-001",
    ))

    tests.append((
        "SODR2 Save accepted owned source",
        saved.source_id
        == "ppct-001",
    ))

    tests.append((
        "SODR3 Stored row scoped by user",
        client.tables[
            "operational_data_sources"
        ].rows[0]["user_id"]
        == "teacher-001",
    ))

    tests.append((
        "SODR4 Get returns owned source",
        repository.get(
            source_id="ppct-001"
        )
        == saved,
    ))

    tests.append((
        "SODR5 Missing get returns None",
        repository.get(
            source_id="missing"
        )
        is None,
    ))

    timetable = make_source(
        source_id="tkb-001",
        data_type=(
            OperationalDataType.TIMETABLE
        ),
    )

    repository.save(
        source=timetable
    )

    week = make_source(
        source_id="week-001",
        data_type=(
            OperationalDataType.ACADEMIC_WEEK
        ),
        status=(
            OperationalDataStatus.VALIDATED
        ),
    )

    repository.save(
        source=week
    )

    tests.append((
        "SODR6 List filters owner",
        tuple(
            source.source_id
            for source
            in repository.list_sources(
                owner_id="teacher-001"
            )
        )
        == (
            "ppct-001",
            "tkb-001",
            "week-001",
        ),
    ))

    tests.append((
        "SODR7 Foreign owner query isolated",
        repository.list_sources(
            owner_id="teacher-999"
        )
        == (),
    ))

    tests.append((
        "SODR8 Academic year filter works",
        len(
            repository.list_sources(
                owner_id="teacher-001",
                academic_year="2026-2027",
            )
        )
        == 3,
    ))

    tests.append((
        "SODR9 Data type filter works",
        repository.list_sources(
            owner_id="teacher-001",
            academic_year="2026-2027",
            data_type=(
                OperationalDataType.TIMETABLE
            ),
        )
        == (
            timetable,
        ),
    ))

    tests.append((
        "SODR10 Status filter works",
        repository.list_sources(
            owner_id="teacher-001",
            academic_year="2026-2027",
            status=(
                OperationalDataStatus.ACTIVE
            ),
        )
        == (
            ppct,
            timetable,
        ),
    ))

    foreign_source = make_source(
        source_id="foreign",
        owner_id="teacher-999",
    )

    tests.append((
        "SODR11 Foreign owner save blocked",
        expect_error(
            ValueError,
            lambda: repository.save(
                source=foreign_source
            ),
        ),
    ))

    client.tables[
        "operational_data_sources"
    ].rows.append(
        {
            "user_id": "teacher-001",
            "source_id": "bad-owner",
            "data_type": "PPCT",
            "origin": "FILE_IMPORTED",
            "owner_id": "teacher-999",
            "academic_year": "2026-2027",
            "status": "ACTIVE",
            "source_name": "bad-owner",
            "source_version": "1",
        }
    )

    tests.append((
        "SODR12 Foreign owner row detected",
        expect_error(
            ValueError,
            lambda: repository.get(
                source_id="bad-owner"
            ),
        ),
    ))

    # Remove the intentionally corrupted fixture after the
    # isolation check so later repository tests inspect only
    # valid rows.
    client.tables[
        "operational_data_sources"
    ].rows = [
        row
        for row
        in client.tables[
            "operational_data_sources"
        ].rows
        if row.get("source_id") != "bad-owner"
    ]

    repository.delete(
        source_id="tkb-001"
    )

    tests.append((
        "SODR13 Delete removes owned source",
        repository.get(
            source_id="tkb-001"
        )
        is None,
    ))

    tests.append((
        "SODR14 Delete leaves other sources",
        repository.get(
            source_id="ppct-001"
        )
        is not None,
    ))

    updated_ppct = OperationalDataSource(
        source_id="ppct-001",
        data_type=OperationalDataType.PPCT,
        origin=OperationalDataOrigin.FILE_IMPORTED,
        owner_id="teacher-001",
        academic_year="2026-2027",
        status=OperationalDataStatus.SUPERSEDED,
        source_name="PPCT updated",
        source_version="2",
    )

    repository.save(
        source=updated_ppct
    )

    tests.append((
        "SODR15 Upsert updates existing identity",
        (
            repository.get(
                source_id="ppct-001"
            ).source_version
            == "2"
        ),
    ))

    tests.append((
        "SODR16 Adapter stores metadata only",
        all(
            "payload" not in row
            and
            "workbook_bytes" not in row
            and
            "schedule_data" not in row
            for row
            in client.tables[
                "operational_data_sources"
            ].rows
        ),
    ))

    tests.append((
        "SODR17 List returns tuple",
        isinstance(
            repository.list_sources(),
            tuple,
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
            "RESULT: PASS - SUPABASE "
            "OPERATIONAL DATA SOURCE "
            "REPOSITORY VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - SUPABASE "
        "OPERATIONAL DATA SOURCE "
        "REPOSITORY VIOLATED"
    )

    return False


def test_supabase_operational_data_source_repository():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
