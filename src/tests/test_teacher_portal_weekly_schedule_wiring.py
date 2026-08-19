from __future__ import annotations

import inspect

import scripts.teacher_portal.app as teacher_portal_app


def run_contract():
    print("=" * 72)
    print(
        "MVP-OPS-003A.3D - "
        "TEACHER PORTAL WEEKLY SCHEDULE WIRING TEST"
    )
    print("=" * 72)

    tests = []

    source = inspect.getsource(
        teacher_portal_app
    )

    tests.append((
        "TPW1 Weekly schedule remains a Teacher Portal page",
        "L\u1ecbch b\u00e1o gi\u1ea3ng"
        in teacher_portal_app.PORTAL_PAGES,
    ))

    tests.append((
        "TPW2 V2 Streamlit renderer referenced",
        (
            "portal_v2.ui.weekly_schedule_streamlit"
            in source
            and
            "render_weekly_schedule_workspace"
            in source
        ),
    ))

    tests.append((
        "TPW3 Legacy weekly app no longer wired",
        (
            "from scripts.weekly_schedule.app "
            "import main as render_weekly_schedule"
            not in source
        ),
    ))

    tests.append((
        "TPW4 Weekly page invokes V2 renderer",
        (
            "render_weekly_schedule_workspace("
            in source
            and "client=client"
            in source
            and "user_id=str(user_id)"
            in source
        ),
    ))

    tests.append((
        "TPW5 Weekly schedule remains in portal navigation",
        "L\u1ecbch b\u00e1o gi\u1ea3ng"
        in teacher_portal_app.PORTAL_PAGES,
    ))

    tests.append((
        "TPW6 Admin shell remains separate",
        "render_admin_shell"
        in source,
    ))

    tests.append((
        "TPW7 Weekly renderer is not wired into ADMIN shell",
        "render_weekly_schedule_workspace"
        not in inspect.getsource(
            __import__(
                "portal_v2.ui.admin_shell",
                fromlist=["*"],
            )
        ),
    ))

    tests.append((
        "TPW8 Teacher Portal owns no workbook parser",
        "load_workbook"
        not in source,
    ))

    tests.append((
        "TPW9 Teacher Portal owns no schedule engine logic",
        not any(
            token
            in source
            for token in (
                "completed_counts",
                "curriculum_index",
                "_completed_counts",
            )
        ),
    ))

    tests.append((
        "TPW10 Teacher Portal owns no Excel rendering",
        not any(
            token
            in source
            for token in (
                "Workbook(",
                "PatternFill",
                "Font(",
                "Alignment(",
                "merge_cells",
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
            "RESULT: PASS - TEACHER PORTAL "
            "WEEKLY SCHEDULE WIRING VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - TEACHER PORTAL "
        "WEEKLY SCHEDULE WIRING VIOLATED"
    )

    return False


def test_teacher_portal_weekly_schedule_wiring():
    assert run_contract()


def main():
    raise SystemExit(
        0 if run_contract() else 1
    )


if __name__ == "__main__":
    main()
