from dataclasses import FrozenInstanceError
import inspect

from portal_v2.authorization import (
    PORTAL_ROLE_ADMIN,
    PORTAL_ROLE_TEACHER,
    PortalRoleResolution,
    TrustedPortalRoleSource,
)


def expect_error(
    error_type,
    action,
):
    try:
        action()
    except error_type:
        return True
    except Exception:
        return False

    return False


def main():
    print("=" * 72)
    print(
        "WR-001E.2D.3B - "
        "TRUSTED PORTAL ROLE SOURCE CONTRACT TEST"
    )
    print("=" * 72)

    tests = []

    trusted_admin = PortalRoleResolution(
        user_id="USER-ADMIN",
        role="admin",
        source_ref="AUTHZ-SOURCE",
        trusted=True,
    )

    trusted_teacher = PortalRoleResolution(
        user_id="USER-TEACHER",
        role="teacher",
        source_ref="AUTHZ-SOURCE",
        trusted=True,
    )

    untrusted_admin = PortalRoleResolution(
        user_id="USER-UNKNOWN",
        role="admin",
        source_ref="UNTRUSTED-SOURCE",
        trusted=False,
    )

    tests.append((
        "PRS1 Trusted admin resolution accepted",
        isinstance(
            trusted_admin,
            PortalRoleResolution,
        ),
    ))

    tests.append((
        "PRS2 Role normalized",
        PortalRoleResolution(
            user_id="USER",
            role=" ADMIN ",
            source_ref="SOURCE",
            trusted=True,
        ).role
        == PORTAL_ROLE_ADMIN,
    ))

    tests.append((
        "PRS3 Trusted admin grants admin access",
        trusted_admin.grants_admin_access
        is True,
    ))

    tests.append((
        "PRS4 Trusted teacher does not grant admin",
        trusted_teacher.grants_admin_access
        is False,
    ))

    tests.append((
        "PRS5 Untrusted admin cannot grant admin",
        untrusted_admin.grants_admin_access
        is False,
    ))

    tests.append((
        "PRS6 Untrusted admin falls back to teacher",
        untrusted_admin.effective_role
        == PORTAL_ROLE_TEACHER,
    ))

    tests.append((
        "PRS7 Trusted admin effective role preserved",
        trusted_admin.effective_role
        == PORTAL_ROLE_ADMIN,
    ))

    tests.append((
        "PRS8 Trusted teacher effective role preserved",
        trusted_teacher.effective_role
        == PORTAL_ROLE_TEACHER,
    ))

    tests.append((
        "PRS9 Unknown role blocked",
        expect_error(
            ValueError,
            lambda: PortalRoleResolution(
                user_id="USER",
                role="owner",
                source_ref="SOURCE",
                trusted=True,
            ),
        ),
    ))

    tests.append((
        "PRS10 Empty user ID blocked",
        expect_error(
            ValueError,
            lambda: PortalRoleResolution(
                user_id=" ",
                role="teacher",
                source_ref="SOURCE",
                trusted=True,
            ),
        ),
    ))

    tests.append((
        "PRS11 Empty source ref blocked",
        expect_error(
            ValueError,
            lambda: PortalRoleResolution(
                user_id="USER",
                role="teacher",
                source_ref=" ",
                trusted=True,
            ),
        ),
    ))

    tests.append((
        "PRS12 Invalid trusted flag blocked",
        expect_error(
            TypeError,
            lambda: PortalRoleResolution(
                user_id="USER",
                role="teacher",
                source_ref="SOURCE",
                trusted=1,
            ),
        ),
    ))

    tests.append((
        "PRS13 Resolution immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                trusted_admin,
                "role",
                "teacher",
            ),
        ),
    ))

    tests.append((
        "PRS14 Role source contract is abstract",
        bool(
            getattr(
                TrustedPortalRoleSource,
                "__abstractmethods__",
                (),
            )
        ),
    ))

    tests.append((
        "PRS15 Abstract source cannot instantiate",
        expect_error(
            TypeError,
            lambda: TrustedPortalRoleSource(),
        ),
    ))

    source = inspect.getsource(
        TrustedPortalRoleSource
    )

    tests.append((
        "PRS16 Contract contains no Supabase dependency",
        all(
            token not in source
            for token in (
                "import supabase",
                "from supabase",
                "create_client(",
                ".table(",
            )
        ),
    ))

    tests.append((
        "PRS17 Contract contains no physical storage dependency",
        all(
            token not in source.lower()
            for token in (
                "sqlite",
                "postgres",
                "open(",
                "path(",
                "json.load",
            )
        ),
    ))

    resolution_source = inspect.getsource(
        PortalRoleResolution
    )

    tests.append((
        "PRS18 Contract contains no email-based authorization",
        all(
            token not in resolution_source.lower()
            for token in (
                "email ==",
                "email.endswith",
                "email.startswith",
                "@gmail.com",
                "@yahoo.com",
                "admin@",
            )
        ),
    ))

    tests.append((
        "PRS19 Contract contains no educational values",
        all(
            token not in resolution_source
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

    tests.append((
        "PRS20 Fail-safe default is teacher",
        PortalRoleResolution(
            user_id="USER-X",
            role="admin",
            source_ref="SOURCE-X",
            trusted=False,
        ).effective_role
        == PORTAL_ROLE_TEACHER,
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
            "RESULT: PASS - TRUSTED PORTAL "
            "ROLE SOURCE CONTRACT VERIFIED"
        )
        raise SystemExit(0)

    print(
        "RESULT: FAIL - TRUSTED PORTAL "
        "ROLE SOURCE CONTRACT VIOLATED"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()

