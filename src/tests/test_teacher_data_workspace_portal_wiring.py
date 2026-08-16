from __future__ import annotations

import inspect

import scripts.teacher_portal.app as teacher_portal_app


def run_contract() -> bool:
    print("=" * 72)
    print(
        "MVP-OPS-003B.4B - "
        "TEACHER DATA WORKSPACE PORTAL WIRING TEST"
    )
    print("=" * 72)

    source = inspect.getsource(
        teacher_portal_app
    )

    tests = []

    tests.append((
        "TDWW1 Teacher data page registered",
        "D\u1eef li\u1ec7u c\u1ee7a t\u00f4i"
        in teacher_portal_app.PORTAL_PAGES,
    ))

    tests.append((
        "TDWW2 Navigation contains six pages",
        len(
            teacher_portal_app.PORTAL_PAGES
        ) == 6,
    ))

    tests.append((
        "TDWW3 Workspace model wired",
        "TeacherOperationalDataWorkspace"
        in source,
    ))

    tests.append((
        "TDWW4 Workspace presenter wired",
        "TeacherDataWorkspacePresenter"
        in source,
    ))

    tests.append((
        "TDWW5 Workspace renderer wired",
        (
            "render_teacher_data_workspace"
            in source
            and
            "render_teacher_data_workspace("
            in source
        ),
    ))

    tests.append((
        "TDWW6 Owner uses authenticated user",
        "owner_id=str(user_id)"
        in source,
    ))

    tests.append((
        "TDWW7 Academic year is user supplied",
        (
            'key="teacher_data_academic_year"'
            in source
        ),
    ))

    tests.append((
        "TDWW8 No fixed academic year assignment",
        'academic_year="2026-2027"'
        not in source,
    ))

    tests.append((
        "TDWW9 Workspace renderer remains outside ADMIN",
        "render_teacher_data_workspace"
        not in inspect.getsource(
            __import__(
                "portal_v2.ui.admin_shell",
                fromlist=["*"],
            )
        ),
    ))

    tests.append((
        "TDWW10 Teacher Portal owns no operational repository",
        "OperationalDataSourceRepository"
        not in source,
    ))

    tests.append((
        "TDWW11 Teacher data branch owns no Supabase persistence",
        "SupabaseOperationalDataSourceRepository"
        not in source,
    ))

    tests.append((
        "TDWW12 Teacher Portal owns no workbook parser",
        "load_workbook"
        not in source,
    ))

    tests.append((
        "TDWW13 Teacher Portal owns no workbook rendering",
        not any(
            token
            in source
            for token in (
                "Workbook(",
                "PatternFill",
                "merge_cells",
            )
        ),
    ))

    tests.append((
        "TDWW14 Weekly Schedule V2 wiring preserved",
        (
            "render_weekly_schedule_workspace"
            in source
            and
            "from scripts.weekly_schedule.app "
            "import main as render_weekly_schedule"
            not in source
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
            "WORKSPACE PORTAL WIRING VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - TEACHER DATA "
        "WORKSPACE PORTAL WIRING VIOLATED"
    )

    return False


def test_teacher_data_workspace_portal_wiring():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
