from __future__ import annotations

import inspect

from educational_planning_v2.models.operational_data_io import (
    OperationalInputLocation,
    OperationalInputReference,
)
from educational_planning_v2.models.operational_data_source import (
    OperationalDataOrigin,
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.repositories.operational_data_source_repository import (
    OperationalDataSourceRepository,
)
from educational_planning_v2.services.operational_input_selection_service import (
    OperationalInputSelection,
    OperationalInputSelectionService,
)


class FakeOperationalDataSourceRepository(
    OperationalDataSourceRepository
):
    def __init__(
        self,
        sources: tuple[OperationalDataSource, ...] = (),
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
        return self._sources.get(
            source_id
        )

    def list_sources(
        self,
        *,
        owner_id: str | None = None,
        academic_year: str | None = None,
        data_type: OperationalDataType | None = None,
        status: OperationalDataStatus | None = None,
    ) -> tuple[OperationalDataSource, ...]:
        result = tuple(
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

        return tuple(
            sorted(
                result,
                key=lambda item: item.source_id,
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
    source_id: str = "PPCT-2026",
    academic_year: str = "2026-2027",
    status: OperationalDataStatus = OperationalDataStatus.ACTIVE,
) -> OperationalDataSource:
    return OperationalDataSource(
        source_id=source_id,
        data_type=OperationalDataType.PPCT,
        origin=OperationalDataOrigin.FILE_IMPORTED,
        owner_id="GV001",
        academic_year=academic_year,
        status=status,
        source_name="PPCT",
        source_version="v1",
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
        "MVP-OPS-002A - "
        "OPERATIONAL INPUT SELECTION SERVICE TEST"
    )
    print("=" * 72)

    active_source = make_source()

    repository = FakeOperationalDataSourceRepository(
        (
            active_source,
        )
    )

    service = OperationalInputSelectionService(
        repository
    )

    tests = []

    local_reference = OperationalInputReference(
        location=OperationalInputLocation.LOCAL_UPLOAD,
    )

    local_selection = service.select(
        reference=local_reference,
    )

    tests.append((
        "OIS1 Local upload selection accepted",
        isinstance(
            local_selection,
            OperationalInputSelection,
        ),
    ))

    tests.append((
        "OIS2 Local upload owns no catalog source",
        local_selection.source is None,
    ))

    library_reference = OperationalInputReference(
        location=OperationalInputLocation.SYSTEM_LIBRARY,
        source_id="PPCT-2026",
        source_academic_year="2026-2027",
    )

    library_selection = service.select(
        reference=library_reference,
    )

    tests.append((
        "OIS3 System library source resolved",
        library_selection.source
        is active_source,
    ))

    tests.append((
        "OIS4 Source identity preserved",
        library_selection.source.source_id
        == "PPCT-2026",
    ))

    tests.append((
        "OIS5 Source academic year preserved",
        library_selection.source.academic_year
        == "2026-2027",
    ))

    tests.append((
        "OIS6 Only ACTIVE source consumed",
        library_selection.source.status
        is OperationalDataStatus.ACTIVE,
    ))

    missing_reference = OperationalInputReference(
        location=OperationalInputLocation.SYSTEM_LIBRARY,
        source_id="MISSING",
        source_academic_year="2026-2027",
    )

    tests.append((
        "OIS7 Missing library source blocked",
        expect_error(
            LookupError,
            lambda: service.select(
                reference=missing_reference,
            ),
        ),
    ))

    pending_source = make_source(
        source_id="PPCT-PENDING",
        status=OperationalDataStatus.VALIDATED,
    )

    pending_service = OperationalInputSelectionService(
        FakeOperationalDataSourceRepository(
            (
                pending_source,
            )
        )
    )

    pending_reference = OperationalInputReference(
        location=OperationalInputLocation.SYSTEM_LIBRARY,
        source_id="PPCT-PENDING",
        source_academic_year="2026-2027",
    )

    tests.append((
        "OIS8 Non-ACTIVE library source blocked",
        expect_error(
            ValueError,
            lambda: pending_service.select(
                reference=pending_reference,
            ),
        ),
    ))

    wrong_year_reference = OperationalInputReference(
        location=OperationalInputLocation.SYSTEM_LIBRARY,
        source_id="PPCT-2026",
        source_academic_year="2025-2026",
    )

    tests.append((
        "OIS9 Academic year mismatch blocked",
        expect_error(
            ValueError,
            lambda: service.select(
                reference=wrong_year_reference,
            ),
        ),
    ))

    generated_reference = OperationalInputReference(
        location=OperationalInputLocation.SYSTEM_GENERATED,
    )

    generated_selection = service.select(
        reference=generated_reference,
    )

    tests.append((
        "OIS10 System-generated reference supported",
        (
            generated_selection.reference.location
            is OperationalInputLocation.SYSTEM_GENERATED
            and
            generated_selection.source is None
        ),
    ))

    tests.append((
        "OIS11 Wrong reference type blocked",
        expect_error(
            TypeError,
            lambda: service.select(
                reference="LOCAL_UPLOAD",
            ),
        ),
    ))

    tests.append((
        "OIS12 Wrong repository type blocked",
        expect_error(
            TypeError,
            lambda: OperationalInputSelectionService(
                object()
            ),
        ),
    ))

    tests.append((
        "OIS13 SYSTEM_LIBRARY selection requires source",
        expect_error(
            ValueError,
            lambda: OperationalInputSelection(
                reference=library_reference,
                source=None,
            ),
        ),
    ))

    tests.append((
        "OIS14 LOCAL_UPLOAD selection rejects catalog source",
        expect_error(
            ValueError,
            lambda: OperationalInputSelection(
                reference=local_reference,
                source=active_source,
            ),
        ),
    ))

    service_source = inspect.getsource(
        OperationalInputSelectionService
    )

    forbidden_physical_dependencies = (
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
        "OIS15 Service owns no physical I/O dependency",
        not any(
            token.lower()
            in service_source.lower()
            for token
            in forbidden_physical_dependencies
        ),
    ))

    tests.append((
        "OIS16 Service uses repository boundary",
        "_repository.get"
        in service_source,
    ))

    tests.append((
        "OIS17 Service contains no educational payload fields",
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
        "OIS18 Selection is data-type neutral",
        not any(
            token
            in service_source
            for token in (
                "OperationalDataType.PPCT",
                "OperationalDataType.TIMETABLE",
                "OperationalDataType.ACADEMIC_WEEK",
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
            "RESULT: PASS - OPERATIONAL INPUT "
            "SELECTION SERVICE VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - OPERATIONAL INPUT "
        "SELECTION SERVICE VIOLATED"
    )

    return False


def test_operational_input_selection_service():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
