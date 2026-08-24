from __future__ import annotations

from dataclasses import FrozenInstanceError
import inspect

from educational_planning_v2.models.operational_data_source import (
    OperationalDataOrigin,
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.models.teacher_operational_data_workspace import (
    TeacherOperationalDataWorkspace,
)


def source(
    *,
    source_id: str,
    data_type: OperationalDataType,
    owner_id: str = "teacher-001",
    academic_year: str = "2026-2027",
) -> OperationalDataSource:
    return OperationalDataSource(
        source_id=source_id,
        data_type=data_type,
        origin=OperationalDataOrigin.FILE_IMPORTED,
        owner_id=owner_id,
        academic_year=academic_year,
        status=OperationalDataStatus.ACTIVE,
        source_name=source_id,
        source_version="1",
    )


def expect_error(error_type, action) -> bool:
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
        "MVP-OPS-003B.1 - "
        "TEACHER OPERATIONAL DATA WORKSPACE CONTRACT TEST"
    )
    print("=" * 72)

    tests = []

    ppct = source(
        source_id="ppct-001",
        data_type=OperationalDataType.PPCT,
    )

    timetable = source(
        source_id="tkb-001",
        data_type=OperationalDataType.TIMETABLE,
    )

    academic_week = source(
        source_id="week-001",
        data_type=OperationalDataType.ACADEMIC_WEEK,
    )

    workspace = TeacherOperationalDataWorkspace(
        owner_id=" teacher-001 ",
        academic_year=" 2026-2027 ",
        ppct_source=ppct,
        timetable_source=timetable,
        academic_week_source=academic_week,
    )

    tests.append((
        "TDW1 Workspace accepted",
        isinstance(
            workspace,
            TeacherOperationalDataWorkspace,
        ),
    ))

    tests.append((
        "TDW2 Owner normalized",
        workspace.owner_id == "teacher-001",
    ))

    tests.append((
        "TDW3 Academic year normalized",
        workspace.academic_year == "2026-2027",
    ))

    tests.append((
        "TDW4 PPCT source preserved",
        workspace.ppct_source is ppct,
    ))

    tests.append((
        "TDW5 Timetable source preserved",
        workspace.timetable_source is timetable,
    ))

    tests.append((
        "TDW6 Academic week source preserved",
        workspace.academic_week_source is academic_week,
    ))

    tests.append((
        "TDW7 Source lookup works",
        (
            workspace.source_for(
                OperationalDataType.PPCT
            )
            is ppct
            and
            workspace.source_for(
                OperationalDataType.TIMETABLE
            )
            is timetable
            and
            workspace.source_for(
                OperationalDataType.ACADEMIC_WEEK
            )
            is academic_week
        ),
    ))

    tests.append((
        "TDW8 Available sources immutable tuple",
        workspace.available_sources()
        == (
            ppct,
            timetable,
            academic_week,
        ),
    ))

    empty_workspace = TeacherOperationalDataWorkspace(
        owner_id="teacher-001",
        academic_year="2026-2027",
    )

    tests.append((
        "TDW9 Partial workspace allowed",
        empty_workspace.available_sources() == (),
    ))

    tests.append((
        "TDW10 Wrong PPCT type blocked",
        expect_error(
            ValueError,
            lambda: TeacherOperationalDataWorkspace(
                owner_id="teacher-001",
                academic_year="2026-2027",
                ppct_source=timetable,
            ),
        ),
    ))

    foreign_owner = source(
        source_id="ppct-other-owner",
        data_type=OperationalDataType.PPCT,
        owner_id="teacher-999",
    )

    tests.append((
        "TDW11 Foreign owner blocked",
        expect_error(
            ValueError,
            lambda: TeacherOperationalDataWorkspace(
                owner_id="teacher-001",
                academic_year="2026-2027",
                ppct_source=foreign_owner,
            ),
        ),
    ))

    foreign_year = source(
        source_id="ppct-other-year",
        data_type=OperationalDataType.PPCT,
        academic_year="2025-2026",
    )

    tests.append((
        "TDW12 Different academic year blocked",
        expect_error(
            ValueError,
            lambda: TeacherOperationalDataWorkspace(
                owner_id="teacher-001",
                academic_year="2026-2027",
                ppct_source=foreign_year,
            ),
        ),
    ))

    tests.append((
        "TDW13 Empty owner blocked",
        expect_error(
            ValueError,
            lambda: TeacherOperationalDataWorkspace(
                owner_id=" ",
                academic_year="2026-2027",
            ),
        ),
    ))

    tests.append((
        "TDW14 Empty academic year blocked",
        expect_error(
            ValueError,
            lambda: TeacherOperationalDataWorkspace(
                owner_id="teacher-001",
                academic_year=" ",
            ),
        ),
    ))

    tests.append((
        "TDW15 Invalid source lookup type blocked",
        expect_error(
            TypeError,
            lambda: workspace.source_for("PPCT"),
        ),
    ))

    tests.append((
        "TDW16 Unsupported operational type blocked",
        expect_error(
            ValueError,
            lambda: workspace.source_for(
                OperationalDataType.WEEKLY_SCHEDULE_TEMPLATE
            ),
        ),
    ))

    tests.append((
        "TDW17 Workspace immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                workspace,
                "owner_id",
                "teacher-002",
            ),
        ),
    ))

    module_source = inspect.getsource(
        inspect.getmodule(
            TeacherOperationalDataWorkspace
        )
    )

    lower_source = module_source.lower()

    tests.append((
        "TDW18 Workspace owns no payload",
        not any(
            token
            in lower_source
            for token in (
                "payload",
                "workbook_bytes",
                "document_bytes",
            )
        ),
    ))

    tests.append((
        "TDW19 Workspace owns no persistence dependency",
        not any(
            token
            in lower_source
            for token in (
                "sqlite3",
                "supabase",
                "repository",
                "googleapiclient",
            )
        ),
    ))

    tests.append((
        "TDW20 Workspace owns no Streamlit dependency",
        "streamlit"
        not in lower_source,
    ))

    tests.append((
        "TDW21 Workspace owns no workbook parser",
        not any(
            token
            in lower_source
            for token in (
                "openpyxl",
                "load_workbook",
                "workbook(",
            )
        ),
    ))

    tests.append((
        "TDW22 Workspace contains no fixed educational values",
        not any(
            token
            in module_source
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
            "RESULT: PASS - TEACHER OPERATIONAL "
            "DATA WORKSPACE VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - TEACHER OPERATIONAL "
        "DATA WORKSPACE VIOLATED"
    )

    return False


def test_teacher_operational_data_workspace():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
