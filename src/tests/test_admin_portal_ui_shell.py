import inspect

from portal_v2.authorization import (
    PORTAL_ROLE_ADMIN,
    PORTAL_ROLE_TEACHER,
    build_portal_authorization_context,
)
from portal_v2.ui import (
    ADMIN_PAGE_DASHBOARD,
    ADMIN_PAGE_SYSTEM_HEALTH,
    ADMIN_PORTAL_SESSION_KEY,
    admin_page_id_from_label,
    admin_page_label_from_id,
    select_admin_portal_page,
)


def main():
    print("=" * 72)
    print(
        "WR-001E.2D.2 - "
        "STREAMLIT ADMIN UI SHELL TEST"
    )
    print("=" * 72)

    tests = []

    admin = build_portal_authorization_context(
        user_id="ADMIN-TEST",
        email="admin@example.test",
        role=PORTAL_ROLE_ADMIN,
    )

    teacher = build_portal_authorization_context(
        user_id="TEACHER-TEST",
        email="teacher@example.test",
        role=PORTAL_ROLE_TEACHER,
    )

    tests.append((
        "AUS1 Admin authorization can access shell",
        admin.can_access_admin_portal is True,
    ))

    tests.append((
        "AUS2 Teacher authorization cannot access shell",
        teacher.can_access_admin_portal is False,
    ))

    tests.append((
        "AUS3 Dashboard label resolves",
        admin_page_label_from_id(
            page_id=ADMIN_PAGE_DASHBOARD
        )
        == "Dashboard",
    ))

    tests.append((
        "AUS4 Dashboard ID resolves from label",
        admin_page_id_from_label(
            label="Dashboard"
        )
        == ADMIN_PAGE_DASHBOARD,
    ))

    state = {}

    select_admin_portal_page(
        state,
        page_id=ADMIN_PAGE_SYSTEM_HEALTH,
    )

    tests.append((
        "AUS5 Admin page selection stored by canonical ID",
        state[ADMIN_PORTAL_SESSION_KEY]
        == ADMIN_PAGE_SYSTEM_HEALTH,
    ))

    import scripts.teacher_portal.app as teacher_portal_app

    app_source = inspect.getsource(
        teacher_portal_app
    )

    tests.append((
        "AUS6 Teacher portal integrates authorization boundary",
        "build_current_portal_authorization"
        in app_source,
    ))

    tests.append((
        "AUS7 ADMIN visibility uses authorization capability",
        "authorization.can_access_admin_portal"
        in app_source,
    ))

    tests.append((
        "AUS8 ADMIN shell integrated",
        "render_admin_shell"
        in app_source,
    ))

    tests.append((
        "AUS9 Portal does not hard-code admin email",
        (
            "if email ==" not in app_source
            and
            "admin@gmail" not in app_source
            and
            "admin@yahoo" not in app_source
        ),
    ))

    tests.append((
        "AUS10 Portal role is session boundary",
        "portal_user_role"
        in app_source,
    ))

    tests.append((
        "AUS11 Login role comes from trusted role integration",
        (
            "resolve_authenticated_portal_role"
            in app_source
            and
            '["portal_user_role"] = PORTAL_ROLE_TEACHER'
            not in app_source
        ),
    ))

    from portal_v2.ui import admin_shell

    shell_source = inspect.getsource(
        admin_shell
    )

    tests.append((
        "AUS12 Admin shell contains all six canonical sections",
        all(
            text in shell_source
            for text in (
                "ADMIN Dashboard",
                "Trusted Data",
                "Time Allocation",
                "Sources & Provenance",
                "Users & Permissions",
                "System Health",
            )
        ),
    ))

    tests.append((
        "AUS13 Shell contains no physical storage dependency",
        all(
            token not in shell_source.lower()
            for token in (
                "sqlite3",
                "postgres",
                "openpyxl",
                "supabase",
            )
        ),
    ))

    tests.append((
        "AUS14 Shell contains no fixed educational period value",
        all(
            token not in shell_source
            for token in (
                "140",
                "105",
                "70",
                "35",
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
            "RESULT: PASS - STREAMLIT ADMIN UI SHELL VERIFIED"
        )
        raise SystemExit(0)

    print(
        "RESULT: FAIL - STREAMLIT ADMIN UI SHELL VIOLATED"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()

