from __future__ import annotations

from educational_planning_v2.models.operational_data_source import (
    OperationalDataOrigin,
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.models.teacher_operational_data_workspace import (
    TeacherOperationalDataWorkspace,
)
from educational_planning_v2.repositories.operational_data_source_repository import (
    OperationalDataSourceRepository,
)
from educational_planning_v2.services.teacher_operational_data_workspace_service import (
    TeacherOperationalDataWorkspaceRequest,
    TeacherOperationalDataWorkspaceService,
)


class FakeOperationalDataSourceRepository(
    OperationalDataSourceRepository
):
    def __init__(
        self,
        sources: tuple[OperationalDataSource, ...],
    ) -> None:
        self._sources = sources

    def save(
        self,
        *,
        source: OperationalDataSource,
    ) -> OperationalDataSource:
        raise NotImplementedError

    def get(
        self,
        *,
        source_id: str,
    ) -> OperationalDataSource | None:
        return next(
            (
                source
                for source in self._sources
                if source.source_id == source_id
            ),
            None,
        )

    def list_sources(
        self,
        *,
        owner_id: str | None = None,
        academic_year: str | None = None,
        data_type: OperationalDataType | None = None,
        status: OperationalDataStatus | None = None,
    ) -> tuple[OperationalDataSource, ...]:
        result = self._sources

        if owner_id is not None:
            result = tuple(
                source
                for source in result
                if source.owner_id == owner_id
            )

        if academic_year is not None:
            result = tuple(
                source
                for source in result
                if source.academic_year == academic_year
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

        return result

    def delete(
        self,
        *,
        source_id: str,
    ) -> None:
        raise NotImplementedError


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
        "MVP-OPS-003B.2 - "
        "TEACHER OPERATIONAL DATA WORKSPACE SERVICE TEST"
    )
    print("=" * 72)

    active_ppct = make_source(
        source_id="ppct-active",
        data_type=OperationalDataType.PPCT,
        status=OperationalDataStatus.ACTIVE,
    )

    active_timetable = make_source(
        source_id="tkb-active",
        data_type=OperationalDataType.TIMETABLE,
        status=OperationalDataStatus.ACTIVE,
    )

    active_week = make_source(
        source_id="week-active",
        data_type=OperationalDataType.ACADEMIC_WEEK,
        status=OperationalDataStatus.ACTIVE,
    )

    validated_ppct = make_source(
        source_id="ppct-validated",
        data_type=OperationalDataType.PPCT,
        status=OperationalDataStatus.VALIDATED,
    )

    superseded_timetable = make_source(
        source_id="tkb-old",
        data_type=OperationalDataType.TIMETABLE,
        status=OperationalDataStatus.SUPERSEDED,
    )

    foreign_owner_ppct = make_source(
        source_id="ppct-other-owner",
        data_type=OperationalDataType.PPCT,
        status=OperationalDataStatus.ACTIVE,
        owner_id="teacher-999",
    )

    foreign_year_week = make_source(
        source_id="week-other-year",
        data_type=OperationalDataType.ACADEMIC_WEEK,
        status=OperationalDataStatus.ACTIVE,
        academic_year="2025-2026",
    )

    repository = FakeOperationalDataSourceRepository(
        (
            active_ppct,
            active_timetable,
            active_week,
            validated_ppct,
            superseded_timetable,
            foreign_owner_ppct,
            foreign_year_week,
        )
    )

    service = TeacherOperationalDataWorkspaceService(
        repository
    )

    request = TeacherOperationalDataWorkspaceRequest(
        owner_id=" teacher-001 ",
        academic_year=" 2026-2027 ",
    )

    workspace = service.build(
        request=request
    )

    tests = []

    tests.append((
        "TDWS1 Request accepted",
        isinstance(
            request,
            TeacherOperationalDataWorkspaceRequest,
        ),
    ))

    tests.append((
        "TDWS2 Request owner normalized",
        request.owner_id == "teacher-001",
    ))

    tests.append((
        "TDWS3 Request academic year normalized",
        request.academic_year == "2026-2027",
    ))

    tests.append((
        "TDWS4 Workspace produced",
        isinstance(
            workspace,
            TeacherOperationalDataWorkspace,
        ),
    ))

    tests.append((
        "TDWS5 ACTIVE PPCT selected",
        workspace.ppct_source is active_ppct,
    ))

    tests.append((
        "TDWS6 ACTIVE timetable selected",
        workspace.timetable_source
        is active_timetable,
    ))

    tests.append((
        "TDWS7 ACTIVE academic week selected",
        workspace.academic_week_source
        is active_week,
    ))

    tests.append((
        "TDWS8 VALIDATED source ignored",
        workspace.ppct_source
        is not validated_ppct,
    ))

    tests.append((
        "TDWS9 SUPERSEDED source ignored",
        workspace.timetable_source
        is not superseded_timetable,
    ))

    tests.append((
        "TDWS10 Foreign owner isolated",
        workspace.ppct_source
        is not foreign_owner_ppct,
    ))

    tests.append((
        "TDWS11 Foreign academic year isolated",
        workspace.academic_week_source
        is not foreign_year_week,
    ))

    empty_service = (
        TeacherOperationalDataWorkspaceService(
            FakeOperationalDataSourceRepository(())
        )
    )

    empty_workspace = empty_service.build(
        request=TeacherOperationalDataWorkspaceRequest(
            owner_id="teacher-001",
            academic_year="2026-2027",
        )
    )

    tests.append((
        "TDWS12 Missing sources produce partial workspace",
        empty_workspace.available_sources() == (),
    ))

    ambiguous_repository = (
        FakeOperationalDataSourceRepository(
            (
                active_ppct,
                make_source(
                    source_id="ppct-active-2",
                    data_type=OperationalDataType.PPCT,
                    status=OperationalDataStatus.ACTIVE,
                ),
            )
        )
    )

    ambiguous_service = (
        TeacherOperationalDataWorkspaceService(
            ambiguous_repository
        )
    )

    tests.append((
        "TDWS13 Multiple ACTIVE PPCT blocked",
        expect_error(
            ValueError,
            lambda: ambiguous_service.build(
                request=TeacherOperationalDataWorkspaceRequest(
                    owner_id="teacher-001",
                    academic_year="2026-2027",
                )
            ),
        ),
    ))

    tests.append((
        "TDWS14 Wrong repository blocked",
        expect_error(
            TypeError,
            lambda: TeacherOperationalDataWorkspaceService(
                object()
            ),
        ),
    ))

    tests.append((
        "TDWS15 Wrong request blocked",
        expect_error(
            TypeError,
            lambda: service.build(
                request="bad-request"
            ),
        ),
    ))

    tests.append((
        "TDWS16 Empty request owner blocked",
        expect_error(
            ValueError,
            lambda: TeacherOperationalDataWorkspaceRequest(
                owner_id=" ",
                academic_year="2026-2027",
            ),
        ),
    ))

    tests.append((
        "TDWS17 Empty academic year blocked",
        expect_error(
            ValueError,
            lambda: TeacherOperationalDataWorkspaceRequest(
                owner_id="teacher-001",
                academic_year=" ",
            ),
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
            "RESULT: PASS - TEACHER OPERATIONAL "
            "DATA WORKSPACE SERVICE VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - TEACHER OPERATIONAL "
        "DATA WORKSPACE SERVICE VIOLATED"
    )

    return False


def test_teacher_operational_data_workspace_service():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
