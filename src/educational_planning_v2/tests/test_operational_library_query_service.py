from __future__ import annotations

import inspect

from educational_planning_v2.models.operational_data_source import (
    OperationalDataOrigin,
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.repositories.operational_data_source_repository import (
    OperationalDataSourceRepository,
)
from educational_planning_v2.services.operational_library_query_service import (
    OperationalLibraryItem,
    OperationalLibraryQuery,
    OperationalLibraryQueryService,
)


class FakeOperationalDataSourceRepository(
    OperationalDataSourceRepository
):
    def __init__(
        self,
        sources: tuple[OperationalDataSource, ...],
    ) -> None:
        self._sources = {
            source.source_id: source
            for source in sources
        }

    def save(
        self,
        *,
        source: OperationalDataSource,
    ) -> OperationalDataSource:
        self._sources[source.source_id] = source
        return source

    def get(
        self,
        *,
        source_id: str,
    ) -> OperationalDataSource | None:
        return self._sources.get(source_id)

    def list_sources(
        self,
        *,
        owner_id: str | None = None,
        academic_year: str | None = None,
        data_type: OperationalDataType | None = None,
        status: OperationalDataStatus | None = None,
    ) -> tuple[OperationalDataSource, ...]:
        return tuple(
            source
            for source in self._sources.values()
            if (
                owner_id is None
                or source.owner_id == owner_id
            )
            and (
                academic_year is None
                or source.academic_year == academic_year
            )
            and (
                data_type is None
                or source.data_type is data_type
            )
            and (
                status is None
                or source.status is status
            )
        )

    def delete(
        self,
        *,
        source_id: str,
    ) -> None:
        self._sources.pop(
            source_id,
            None,
        )


def make_source(
    *,
    source_id: str,
    owner_id: str,
    academic_year: str,
    data_type: OperationalDataType,
    status: OperationalDataStatus,
    source_name: str,
    source_version: str | None = None,
) -> OperationalDataSource:
    return OperationalDataSource(
        source_id=source_id,
        data_type=data_type,
        origin=OperationalDataOrigin.FILE_IMPORTED,
        owner_id=owner_id,
        academic_year=academic_year,
        status=status,
        source_name=source_name,
        source_version=source_version,
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
        "MVP-OPS-002B - "
        "SYSTEM LIBRARY QUERY SERVICE TEST"
    )
    print("=" * 72)

    sources = (
        make_source(
            source_id="PPCT-A",
            owner_id="GV001",
            academic_year="2026-2027",
            data_type=OperationalDataType.PPCT,
            status=OperationalDataStatus.ACTIVE,
            source_name="PPCT Toan 6",
            source_version="v2",
        ),
        make_source(
            source_id="PPCT-B",
            owner_id="GV001",
            academic_year="2026-2027",
            data_type=OperationalDataType.PPCT,
            status=OperationalDataStatus.ACTIVE,
            source_name="PPCT Toan 6",
            source_version="v1",
        ),
        make_source(
            source_id="PPCT-OLD",
            owner_id="GV001",
            academic_year="2025-2026",
            data_type=OperationalDataType.PPCT,
            status=OperationalDataStatus.ACTIVE,
            source_name="PPCT cu",
        ),
        make_source(
            source_id="TKB-A",
            owner_id="GV001",
            academic_year="2026-2027",
            data_type=OperationalDataType.TIMETABLE,
            status=OperationalDataStatus.ACTIVE,
            source_name="TKB",
        ),
        make_source(
            source_id="PPCT-DRAFT",
            owner_id="GV001",
            academic_year="2026-2027",
            data_type=OperationalDataType.PPCT,
            status=OperationalDataStatus.VALIDATED,
            source_name="PPCT chua kich hoat",
        ),
        make_source(
            source_id="PPCT-OTHER",
            owner_id="GV002",
            academic_year="2026-2027",
            data_type=OperationalDataType.PPCT,
            status=OperationalDataStatus.ACTIVE,
            source_name="PPCT giao vien khac",
        ),
    )

    repository = FakeOperationalDataSourceRepository(
        sources
    )

    service = OperationalLibraryQueryService(
        repository
    )

    tests = []

    query = OperationalLibraryQuery(
        owner_id=" GV001 ",
        academic_year=" 2026-2027 ",
        data_type=OperationalDataType.PPCT,
    )

    tests.append((
        "OLQ1 Query accepted",
        isinstance(
            query,
            OperationalLibraryQuery,
        ),
    ))

    tests.append((
        "OLQ2 Owner normalized",
        query.owner_id == "GV001",
    ))

    tests.append((
        "OLQ3 Academic year normalized",
        query.academic_year == "2026-2027",
    ))

    tests.append((
        "OLQ4 Default status is ACTIVE",
        query.status
        is OperationalDataStatus.ACTIVE,
    ))

    result = service.query(
        query=query,
    )

    tests.append((
        "OLQ5 Active PPCT sources returned",
        len(result) == 2,
    ))

    tests.append((
        "OLQ6 Result items are presentation-safe metadata",
        all(
            isinstance(
                item,
                OperationalLibraryItem,
            )
            for item in result
        ),
    ))

    tests.append((
        "OLQ7 Other academic year excluded",
        all(
            item.academic_year
            == "2026-2027"
            for item in result
        ),
    ))

    tests.append((
        "OLQ8 Other data type excluded",
        all(
            item.data_type
            is OperationalDataType.PPCT
            for item in result
        ),
    ))

    tests.append((
        "OLQ9 Non-active source excluded by default",
        all(
            item.status
            is OperationalDataStatus.ACTIVE
            for item in result
        ),
    ))

    tests.append((
        "OLQ10 Other owner excluded",
        all(
            item.source_id
            != "PPCT-OTHER"
            for item in result
        ),
    ))

    tests.append((
        "OLQ11 Results deterministically ordered",
        tuple(
            item.source_id
            for item in result
        )
        == (
            "PPCT-B",
            "PPCT-A",
        ),
    ))

    history_query = OperationalLibraryQuery(
        owner_id="GV001",
        academic_year="2026-2027",
        data_type=OperationalDataType.PPCT,
        status=OperationalDataStatus.VALIDATED,
    )

    history_result = service.query(
        query=history_query,
    )

    tests.append((
        "OLQ12 Explicit non-active status query supported",
        (
            len(history_result) == 1
            and
            history_result[0].source_id
            == "PPCT-DRAFT"
        ),
    ))

    empty_query = OperationalLibraryQuery(
        owner_id="GV001",
        academic_year="2030-2031",
        data_type=OperationalDataType.PPCT,
    )

    tests.append((
        "OLQ13 Empty library result is safe",
        service.query(
            query=empty_query,
        ) == (),
    ))

    tests.append((
        "OLQ14 Empty owner blocked",
        expect_error(
            ValueError,
            lambda: OperationalLibraryQuery(
                owner_id=" ",
                academic_year="2026-2027",
                data_type=OperationalDataType.PPCT,
            ),
        ),
    ))

    tests.append((
        "OLQ15 Empty academic year blocked",
        expect_error(
            ValueError,
            lambda: OperationalLibraryQuery(
                owner_id="GV001",
                academic_year=" ",
                data_type=OperationalDataType.PPCT,
            ),
        ),
    ))

    tests.append((
        "OLQ16 Wrong data type blocked",
        expect_error(
            TypeError,
            lambda: OperationalLibraryQuery(
                owner_id="GV001",
                academic_year="2026-2027",
                data_type="PPCT",
            ),
        ),
    ))

    tests.append((
        "OLQ17 Wrong status blocked",
        expect_error(
            TypeError,
            lambda: OperationalLibraryQuery(
                owner_id="GV001",
                academic_year="2026-2027",
                data_type=OperationalDataType.PPCT,
                status="ACTIVE",
            ),
        ),
    ))

    tests.append((
        "OLQ18 Wrong query type blocked",
        expect_error(
            TypeError,
            lambda: service.query(
                query="bad-query",
            ),
        ),
    ))

    tests.append((
        "OLQ19 Wrong repository blocked",
        expect_error(
            TypeError,
            lambda: OperationalLibraryQueryService(
                object()
            ),
        ),
    ))

    service_source = inspect.getsource(
        OperationalLibraryQueryService
    )

    forbidden_dependencies = (
        "openpyxl",
        "sqlite3",
        "supabase",
        "streamlit",
        "googleapiclient",
        ".xlsx",
        ".docx",
        "open(",
        "Path(",
    )

    tests.append((
        "OLQ20 Service owns no physical storage dependency",
        not any(
            token.lower()
            in service_source.lower()
            for token in forbidden_dependencies
        ),
    ))

    tests.append((
        "OLQ21 Service uses repository list boundary",
        "_repository.list_sources"
        in service_source,
    ))

    tests.append((
        "OLQ22 Service owns no educational payload",
        not any(
            token
            in service_source
            for token in (
                "lesson_title",
                "period_number",
                "teaching_date",
                "timetable_period",
            )
        ),
    ))

    tests.append((
        "OLQ23 Query service is data-type neutral",
        not any(
            token
            in service_source
            for token in (
                "OperationalDataType.PPCT",
                "OperationalDataType.TIMETABLE",
                "OperationalDataType.ACADEMIC_WEEK",
                "OperationalDataType.WEEKLY_SCHEDULE_TEMPLATE",
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
            "RESULT: PASS - SYSTEM LIBRARY "
            "QUERY SERVICE VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - SYSTEM LIBRARY "
        "QUERY SERVICE VIOLATED"
    )

    return False


def test_operational_library_query_service():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
