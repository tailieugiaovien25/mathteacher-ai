import inspect

from portal_v2.authorization import (
    PORTAL_ROLE_ADMIN,
    PORTAL_ROLE_TEACHER,
    PortalRoleResolution,
)
from scripts.teacher_portal.app import (
    build_current_portal_authorization,
    resolve_authenticated_portal_role,
)


class FakeTrustedRoleSource:
    def __init__(self, *, client):
        self.client = client

    def resolve_role(self, *, user_id):
        return PortalRoleResolution(
            user_id=user_id,
            role=PORTAL_ROLE_ADMIN,
            source_ref="TEST_TRUSTED_SOURCE",
            trusted=True,
        )


class FakeFailSafeRoleSource:
    def __init__(self, *, client):
        self.client = client

    def resolve_role(self, *, user_id):
        return PortalRoleResolution(
            user_id=user_id,
            role=PORTAL_ROLE_TEACHER,
            source_ref="TEST_FAIL_SAFE_SOURCE",
            trusted=False,
        )


def main():
    import scripts.teacher_portal.app as app

    print("=" * 72)
    print(
        "WR-001E.2D.3D - "
        "PORTAL LOGIN ROLE INTEGRATION TEST"
    )
    print("=" * 72)

    tests = []

    original_source = app.SupabaseTrustedPortalRoleSource

    try:
        app.SupabaseTrustedPortalRoleSource = FakeTrustedRoleSource
        admin_role = resolve_authenticated_portal_role(
            client=object(),
            user_id="ADMIN-USER",
        )
    finally:
        app.SupabaseTrustedPortalRoleSource = original_source

    tests.append((
        "PLRI1 Trusted admin role reaches login boundary",
        admin_role == PORTAL_ROLE_ADMIN,
    ))

    try:
        app.SupabaseTrustedPortalRoleSource = FakeFailSafeRoleSource
        fallback_role = resolve_authenticated_portal_role(
            client=object(),
            user_id="UNKNOWN-USER",
        )
    finally:
        app.SupabaseTrustedPortalRoleSource = original_source

    tests.append((
        "PLRI2 Untrusted resolution remains teacher",
        fallback_role == PORTAL_ROLE_TEACHER,
    ))

    admin_state = {
        "portal_user_id": "ADMIN-USER",
        "portal_user_email": "person@example.test",
        "portal_user_role": PORTAL_ROLE_ADMIN,
    }

    admin_auth = build_current_portal_authorization(
        admin_state
    )

    tests.append((
        "PLRI3 Resolved admin role grants ADMIN workspace",
        admin_auth.can_access_admin_portal is True,
    ))

    teacher_state = {
        "portal_user_id": "TEACHER-USER",
        "portal_user_email": "teacher@example.test",
        "portal_user_role": PORTAL_ROLE_TEACHER,
    }

    teacher_auth = build_current_portal_authorization(
        teacher_state
    )

    tests.append((
        "PLRI4 Teacher remains outside ADMIN workspace",
        teacher_auth.can_access_admin_portal is False,
    ))

    source = inspect.getsource(app)

    tests.append((
        "PLRI5 Login uses trusted role source",
        "resolve_authenticated_portal_role(" in source
        and "SupabaseTrustedPortalRoleSource" in source,
    ))

    tests.append((
        "PLRI6 Login no longer hard-codes teacher assignment",
        'st.session_state["portal_user_role"] = PORTAL_ROLE_TEACHER'
        not in source,
    ))

    tests.append((
        "PLRI7 Authorization still consumes session role boundary",
        'session_state.get(' in source
        and '"portal_user_role"' in source,
    ))

    tests.append((
        "PLRI8 No email-based ADMIN promotion",
        all(
            token not in source.lower()
            for token in (
                "admin@gmail",
                "admin@yahoo",
                "email.endswith",
                "email.startswith",
            )
        ),
    ))

    tests.append((
        "PLRI9 No user metadata role promotion",
        all(
            token not in source.lower()
            for token in (
                "user_metadata",
                "raw_user_meta_data",
            )
        ),
    ))

    tests.append((
        "PLRI10 Login integration contains no educational values",
        all(
            token not in inspect.getsource(
                resolve_authenticated_portal_role
            )
            for token in (
                "140",
                "105",
                "70",
                "35",
                "KNTT",
                "Toán 6",
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
            "RESULT: PASS - PORTAL LOGIN "
            "ROLE INTEGRATION VERIFIED"
        )
        raise SystemExit(0)

    print(
        "RESULT: FAIL - PORTAL LOGIN "
        "ROLE INTEGRATION VIOLATED"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
