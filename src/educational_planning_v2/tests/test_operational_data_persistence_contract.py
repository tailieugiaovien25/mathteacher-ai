from __future__ import annotations

from educational_planning_v2.models.operational_data_source import (
    OperationalDataOrigin,
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.repositories.operational_data_source_repository import (
    OperationalDataSourceRepository,
)


class InMemoryOperationalDataSourceRepository(
    OperationalDataSourceRepository
):
    def __init__(self) -> None:
        self._sources: dict[str, OperationalDataSource] = {}

    def save(
        self,
        *,
        source: OperationalDataSource,
    ) -> OperationalDataSource:
        if not isinstance(
            source,
            OperationalDataSource,
        ):
            raise TypeError(
                "source must be OperationalDataSource"
            )

        self._sources[source.source_id] = source
        return source

    def get(
        self,
        *,
        source_id: str,
    ) -> OperationalDataSource | None:
        if not isinstance(
            source_id,
            str,
        ):
            raise TypeError(
                "source_id must be str"
            )

        return self._sources.get(
            source_id.strip()
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
            self._sources.values()
        )

        if owner_id is not None:
            result = tuple(
                source
                for source in result
                if source.owner_id == owner_id.strip()
            )

        if academic_year is not None:
            result = tuple(
                source
                for source in result
                if source.academic_year
                == academic_year.strip()
            )

        if data_type is not None:
            result = tuple(
                source
                for source in result
                if source.data_type is data_type
            )

        if status is not None:
            result = tuple(
                source
                for source in result
                if source.status is status
            )

        return tuple(
            sorted(
                result,
                key=lambda source: source.source_id,
            )
        )

    def delete(
        self,
        *,
        source_id: str,
    ) -> None:
        if not isinstance(
            source_id,
            str,
        ):
            raise TypeError(
                "source_id must be str"
            )

        self._sources.pop(
            source_id.strip(),
            None,
        )


def make_source(
    *,
    source_id: str,
    data_type: OperationalDataType,
    status: OperationalDataStatus,
    owner_id: str = "teacher-001",
    academic_year: str = "2026-2027",
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


def run_contract() -> bool:
    print("=" * 72)
    print(
        "MVP-OPS-003B.5A - "
        "OPERATIONAL DATA PERSISTENCE CONTRACT TEST"
    )
    print("=" * 72)

    repository = InMemoryOperationalDataSourceRepository()

    ppct = make_source(
        source_id="ppct-001",
        data_type=OperationalDataType.PPCT,
        status=OperationalDataStatus.ACTIVE,
    )

    timetable = make_source(
        source_id="tkb-001",
        data_type=OperationalDataType.TIMETABLE,
        status=OperationalDataStatus.ACTIVE,
    )

    week = make_source(
        source_id="week-001",
        data_type=OperationalDataType.ACADEMIC_WEEK,
        status=OperationalDataStatus.VALIDATED,
    )

    other_owner = make_source(
        source_id="ppct-other-owner",
        data_type=OperationalDataType.PPCT,
        status=OperationalDataStatus.ACTIVE,
        owner_id="teacher-999",
    )

    other_year = make_source(
        source_id="ppct-other-year",
        data_type=OperationalDataType.PPCT,
        status=OperationalDataStatus.ACTIVE,
        academic_year="2025-2026",
    )

    tests = []

    saved_ppct = repository.save(
        source=ppct
    )

    repository.save(
        source=timetable
    )
    repository.save(
        source=week
    )
    repository.save(
        source=other_owner
    )
    repository.save(
        source=other_year
    )

    tests.append((
        "ODP1 Save returns source",
        saved_ppct is ppct,
    ))

    tests.append((
        "ODP2 Get returns stored source",
        repository.get(
            source_id="ppct-001"
        ) is ppct,
    ))

    tests.append((
        "ODP3 Missing source returns None",
        repository.get(
            source_id="missing"
        ) is None,
    ))

    tests.append((
        "ODP4 Owner filter isolates teacher",
        repository.list_sources(
            owner_id="teacher-001",
        )
        == (
            ppct,
            other_year,
            timetable,
            week,
        ),
    ))

    tests.append((
        "ODP5 Academic year filter isolates year",
        repository.list_sources(
            owner_id="teacher-001",
            academic_year="2026-2027",
        )
        == (
            ppct,
            timetable,
            week,
        ),
    ))

    tests.append((
        "ODP6 Data type filter works",
        repository.list_sources(
            owner_id="teacher-001",
            academic_year="2026-2027",
            data_type=OperationalDataType.PPCT,
        )
        == (
            ppct,
        ),
    ))

    tests.append((
        "ODP7 Status filter works",
        repository.list_sources(
            owner_id="teacher-001",
            academic_year="2026-2027",
            status=OperationalDataStatus.ACTIVE,
        )
        == (
            ppct,
            timetable,
        ),
    ))

    tests.append((
        "ODP8 Combined filters work",
        repository.list_sources(
            owner_id="teacher-001",
            academic_year="2026-2027",
            data_type=OperationalDataType.ACADEMIC_WEEK,
            status=OperationalDataStatus.VALIDATED,
        )
        == (
            week,
        ),
    ))

    repository.delete(
        source_id="tkb-001"
    )

    tests.append((
        "ODP9 Delete removes only target source",
        (
            repository.get(
                source_id="tkb-001"
            )
            is None
            and
            repository.get(
                source_id="ppct-001"
            )
            is ppct
        ),
    ))

    tests.append((
        "ODP10 Delete missing source is safe",
        (
            repository.delete(
                source_id="does-not-exist"
            )
            is None
        ),
    ))

    tests.append((
        "ODP11 Repository contract remains metadata-only",
        not hasattr(
            repository,
            "payload",
        ),
    ))

    tests.append((
        "ODP12 List result is immutable tuple",
        isinstance(
            repository.list_sources(),
            tuple,
        ),
    ))

    tests.append((
        "ODP13 Source identity preserved",
        repository.get(
            source_id="ppct-001"
        ).source_id
        == "ppct-001",
    ))

    tests.append((
        "ODP14 Owner identity preserved",
        repository.get(
            source_id="ppct-001"
        ).owner_id
        == "teacher-001",
    ))

    tests.append((
        "ODP15 Academic year preserved",
        repository.get(
            source_id="ppct-001"
        ).academic_year
        == "2026-2027",
    ))

    tests.append((
        "ODP16 Data type preserved",
        repository.get(
            source_id="ppct-001"
        ).data_type
        is OperationalDataType.PPCT,
    ))

    tests.append((
        "ODP17 Status preserved",
        repository.get(
            source_id="ppct-001"
        ).status
        is OperationalDataStatus.ACTIVE,
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
            "RESULT: PASS - OPERATIONAL DATA "
            "PERSISTENCE CONTRACT VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - OPERATIONAL DATA "
        "PERSISTENCE CONTRACT VIOLATED"
    )

    return False


def test_operational_data_persistence_contract():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
