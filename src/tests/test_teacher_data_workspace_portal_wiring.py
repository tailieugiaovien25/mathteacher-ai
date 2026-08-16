from __future__ import annotations

import inspect

import scripts.teacher_portal.app as teacher_portal_app


def run_contract() -> bool:
    print("=" * 72)
    print(
        "MVP-OPS-003B.5C.3 - "
        "TEACHER DATA WORKSPACE PERSISTENCE WIRING TEST"
    )
    print("=" * 72)

    source = inspect.getsource(
        teacher_portal_app
    )

    lower = source.lower()

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
        "TDWW3 Operational Supabase adapter composed",
        (
            "SupabaseOperationalDataSourceRepository"
            in source
            and
            '"operational_data_source_repository"'
            in source
        ),
    ))

    tests.append((
        "TDWW4 Authenticated client reused",
        (
            "client=client"
            in source
            and
            "user_id=user_id"
            in source
        ),
    ))

    tests.append((
        "TDWW5 Workspace service wired",
        "TeacherOperationalDataWorkspaceService"
        in source,
    ))

    tests.append((
        "TDWW6 Workspace request wired",
        "TeacherOperationalDataWorkspaceRequest"
        in source,
    ))

    tests.append((
        "TDWW7 Workspace repository comes from session",
        (
            'st.session_state.get('
            in source
            and
            '"operational_data_source_repository"'
            in source
        ),
    ))

    tests.append((
        "TDWW8 Authenticated owner preserved",
        "owner_id=str(user_id)"
        in source,
    ))

    tests.append((
        "TDWW9 Academic year remains user supplied",
        'key="teacher_data_academic_year"'
        in source,
    ))

    tests.append((
        "TDWW10 No fixed academic year assignment",
        'academic_year="2026-2027"'
        not in source,
    ))

    tests.append((
        "TDWW11 Presenter remains wired",
        "TeacherDataWorkspacePresenter"
        in source,
    ))

    tests.append((
        "TDWW12 Renderer remains wired",
        "render_teacher_data_workspace"
        in source,
    ))

    tests.append((
        "TDWW13 Empty workspace construction removed",
        (
            "TeacherOperationalDataWorkspace("
            not in source
        ),
    ))

    tests.append((
        "TDWW14 Portal owns no direct Supabase table query",
        not any(
            token
            in source
            for token in (
                '.table("operational_data_sources")',
                ".select(",
                ".insert(",
                ".upsert(",
                ".delete()",
            )
        ),
    ))

    tests.append((
        "TDWW15 Portal owns no workbook parser",
        not any(
            token
            in lower
            for token in (
                "openpyxl",
                "load_workbook",
            )
        ),
    ))

    tests.append((
        "TDWW16 Portal owns no operational payload",
        not any(
            token
            in lower
            for token in (
                "workbook_bytes",
                "document_bytes",
                "operational_payload",
            )
        ),
    ))

    tests.append((
        "TDWW17 Weekly Schedule V2 wiring preserved",
        (
            "render_weekly_schedule_workspace"
            in source
            and
            "from scripts.weekly_schedule.app "
            "import main as render_weekly_schedule"
            not in source
        ),
    ))

    tests.append((
        "TDWW18 ADMIN shell remains separate",
        "render_teacher_data_workspace"
        not in inspect.getsource(
            __import__(
                "portal_v2.ui.admin_shell",
                fromlist=["*"],
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
            "RESULT: PASS - TEACHER DATA WORKSPACE "
            "PERSISTENCE WIRING VERIFIED"
        )
        return True

    print(
        "RESULT: FAIL - TEACHER DATA WORKSPACE "
        "PERSISTENCE WIRING VIOLATED"
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
