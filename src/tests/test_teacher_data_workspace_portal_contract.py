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
from portal_v2.ui.teacher_data_workspace_portal import (
    TeacherDataWorkspaceItemState,
    TeacherDataWorkspaceItemView,
    TeacherDataWorkspacePresenter,
    TeacherDataWorkspaceViewModel,
)


def make_source(
    *,
    source_id: str,
    data_type: OperationalDataType,
    source_name: str,
    source_version: str = "1",
) -> OperationalDataSource:
    return OperationalDataSource(
        source_id=source_id,
        data_type=data_type,
        origin=OperationalDataOrigin.FILE_IMPORTED,
        owner_id="teacher-001",
        academic_year="2026-2027",
        status=OperationalDataStatus.ACTIVE,
        source_name=source_name,
        source_version=source_version,
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
        "MVP-OPS-003B.3 - "
        "TEACHER DATA WORKSPACE PORTAL CONTRACT TEST"
    )
    print("=" * 72)

    ppct = make_source(
        source_id="ppct-001",
        data_type=OperationalDataType.PPCT,
        source_name="PPCT 2026-2027",
    )

    timetable = make_source(
        source_id="tkb-001",
        data_type=OperationalDataType.TIMETABLE,
        source_name="TKB hoc ky I",
    )

    workspace = TeacherOperationalDataWorkspace(
        owner_id="teacher-001",
        academic_year="2026-2027",
        ppct_source=ppct,
        timetable_source=timetable,
        academic_week_source=None,
    )

    presenter = TeacherDataWorkspacePresenter()

    view = presenter.present(
        workspace=workspace
    )

    tests = []

    tests.append((
        "TDWP1 View model produced",
        isinstance(
            view,
            TeacherDataWorkspaceViewModel,
        ),
    ))

    tests.append((
        "TDWP2 Owner preserved",
        view.owner_id == "teacher-001",
    ))

    tests.append((
        "TDWP3 Academic year preserved",
        view.academic_year == "2026-2027",
    ))

    tests.append((
        "TDWP4 Three operational items represented",
        len(view.items) == 3,
    ))

    ppct_item = view.item_for(
        OperationalDataType.PPCT
    )

    timetable_item = view.item_for(
        OperationalDataType.TIMETABLE
    )

    week_item = view.item_for(
        OperationalDataType.ACADEMIC_WEEK
    )

    tests.append((
        "TDWP5 PPCT READY",
        (
            ppct_item.state
            is TeacherDataWorkspaceItemState.READY
            and
            ppct_item.source_id == "ppct-001"
            and
            ppct_item.status
            is OperationalDataStatus.ACTIVE
        ),
    ))

    tests.append((
        "TDWP6 Timetable READY",
        (
            timetable_item.state
            is TeacherDataWorkspaceItemState.READY
            and
            timetable_item.source_id == "tkb-001"
        ),
    ))

    tests.append((
        "TDWP7 Academic week MISSING",
        (
            week_item.state
            is TeacherDataWorkspaceItemState.MISSING
            and
            week_item.source_id is None
            and
            week_item.status is None
        ),
    ))

    tests.append((
        "TDWP8 PPCT label stable",
        ppct_item.label == "PPCT",
    ))

    tests.append((
        "TDWP9 Timetable label present",
        bool(
            timetable_item.label.strip()
        ),
    ))

    tests.append((
        "TDWP10 Academic week label present",
        bool(
            week_item.label.strip()
        ),
    ))

    tests.append((
        "TDWP11 Source metadata presentation-safe",
        (
            ppct_item.source_name
            == "PPCT 2026-2027"
            and
            ppct_item.source_version == "1"
        ),
    ))

    tests.append((
        "TDWP12 Missing item exposes no metadata",
        (
            week_item.source_name is None
            and
            week_item.source_version is None
        ),
    ))

    tests.append((
        "TDWP13 Invalid item lookup blocked",
        expect_error(
            TypeError,
            lambda: view.item_for("PPCT"),
        ),
    ))

    tests.append((
        "TDWP14 Unsupported item lookup blocked",
        expect_error(
            ValueError,
            lambda: view.item_for(
                OperationalDataType.WEEKLY_SCHEDULE_TEMPLATE
            ),
        ),
    ))

    tests.append((
        "TDWP15 Ready item requires ACTIVE source",
        expect_error(
            ValueError,
            lambda: TeacherDataWorkspaceItemView(
                data_type=OperationalDataType.PPCT,
                label="PPCT",
                state=TeacherDataWorkspaceItemState.READY,
                source_id="ppct-x",
                source_name="PPCT",
                source_version="1",
                status=OperationalDataStatus.VALIDATED,
            ),
        ),
    ))

    tests.append((
        "TDWP16 Missing item cannot expose metadata",
        expect_error(
            ValueError,
            lambda: TeacherDataWorkspaceItemView(
                data_type=OperationalDataType.PPCT,
                label="PPCT",
                state=TeacherDataWorkspaceItemState.MISSING,
                source_id="unexpected",
                source_name=None,
                source_version=None,
                status=None,
            ),
        ),
    ))

    tests.append((
        "TDWP17 View model immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                view,
                "academic_year",
                "2027-2028",
            ),
        ),
    ))

    module_source = inspect.getsource(
        inspect.getmodule(
            TeacherDataWorkspacePresenter
        )
    )

    lower_source = module_source.lower()

    tests.append((
        "TDWP18 Presenter owns no Streamlit dependency",
        "streamlit"
        not in lower_source,
    ))

    tests.append((
        "TDWP19 Presenter owns no persistence dependency",
        not any(
            token
            in lower_source
            for token in (
                "supabase",
                "sqlite3",
                "repository",
                "googleapiclient",
            )
        ),
    ))

    tests.append((
        "TDWP20 Presenter owns no payload",
        not any(
            token
            in lower_source
            for token in (
                "workbook_bytes",
                "payload",
                "document_bytes",
            )
        ),
    ))

    tests.append((
        "TDWP21 Presenter owns no workbook parser",
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
        "TDWP22 No fixed educational values",
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
            "RESULT: PASS - TEACHER DATA "
            "WORKSPACE PORTAL CONTRACT VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - TEACHER DATA "
        "WORKSPACE PORTAL CONTRACT VIOLATED"
    )

    return False


def test_teacher_data_workspace_portal_contract():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
