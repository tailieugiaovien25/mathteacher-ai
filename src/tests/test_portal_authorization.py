from dataclasses import FrozenInstanceError
import inspect

from curriculum_v2.governance.administrative_authorization import (
    GovernanceActor,
    GovernancePermission,
)
from portal_v2.authorization import (
    PORTAL_ROLE_ADMIN,
    PORTAL_ROLE_TEACHER,
    PortalAuthorizationContext,
    build_portal_authorization_context,
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
        "WR-001E.2C - "
        "ADMIN PORTAL AUTHORIZATION BOUNDARY TEST"
    )
    print("=" * 72)

    tests = []

    teacher = build_portal_authorization_context(
        user_id="USER-TEACHER",
        email="teacher@example.test",
        role="teacher",
    )

    admin = build_portal_authorization_context(
        user_id="USER-ADMIN",
        email="admin@example.test",
        role="admin",
    )

    tests.append((
        "PAB1 Teacher context accepted",
        isinstance(
            teacher,
            PortalAuthorizationContext,
        ),
    ))

    tests.append((
        "PAB2 Admin context accepted",
        isinstance(
            admin,
            PortalAuthorizationContext,
        ),
    ))

    tests.append((
        "PAB3 Role normalized",
        build_portal_authorization_context(
            user_id="ADMIN-2",
            email="x@example.test",
            role=" ADMIN ",
        ).role
        == PORTAL_ROLE_ADMIN,
    ))

    tests.append((
        "PAB4 Teacher cannot access admin portal",
        teacher.can_access_admin_portal
        is False,
    ))

    tests.append((
        "PAB5 Admin can access admin portal",
        admin.can_access_admin_portal
        is True,
    ))

    teacher_actor = (
        teacher.to_governance_actor()
    )

    admin_actor = (
        admin.to_governance_actor()
    )

    tests.append((
        "PAB6 Governance actor produced",
        isinstance(
            admin_actor,
            GovernanceActor,
        ),
    ))

    tests.append((
        "PAB7 Teacher receives no admin permissions",
        teacher_actor.permissions == (),
    ))

    expected_admin_permissions = {
        GovernancePermission.ENTER_DATA,
        GovernancePermission.VERIFY_DATA,
        GovernancePermission.PUBLISH_DATA,
        GovernancePermission.SUPERSEDE_DATA,
    }

    tests.append((
        "PAB8 Admin governance permissions mapped",
        set(
            admin_actor.permissions
        )
        == expected_admin_permissions,
    ))

    tests.append((
        "PAB9 Actor identity comes from user ID",
        admin_actor.actor_id
        == "USER-ADMIN",
    ))

    tests.append((
        "PAB10 Unknown role blocked",
        expect_error(
            ValueError,
            lambda: build_portal_authorization_context(
                user_id="USER",
                email="user@example.test",
                role="superuser",
            ),
        ),
    ))

    tests.append((
        "PAB11 Empty user ID blocked",
        expect_error(
            ValueError,
            lambda: build_portal_authorization_context(
                user_id=" ",
                email="user@example.test",
                role="teacher",
            ),
        ),
    ))

    tests.append((
        "PAB12 Empty email blocked",
        expect_error(
            ValueError,
            lambda: build_portal_authorization_context(
                user_id="USER",
                email=" ",
                role="teacher",
            ),
        ),
    ))

    tests.append((
        "PAB13 Context immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                admin,
                "role",
                "teacher",
            ),
        ),
    ))

    source = inspect.getsource(
        PortalAuthorizationContext
    )

    tests.append((
        "PAB14 Authorization does not hard-code user email",
        (
            "@gmail.com" not in source
            and
            "@yahoo.com" not in source
            and
            "admin@" not in source
        ),
    ))

    factory_source = inspect.getsource(
        build_portal_authorization_context
    )

    tests.append((
        "PAB15 Role is supplied, never inferred from email",
        (
            "role=role" in factory_source
            and
            "email ==" not in factory_source
            and
            "email.endswith" not in factory_source
        ),
    ))

    forbidden_storage_tokens = (
        "sqlite3",
        "supabase",
        "postgres",
        "json.load",
        "open(",
        "Path(",
    )

    combined_source = (
        source
        + factory_source
    )

    tests.append((
        "PAB16 Authorization boundary is storage-neutral",
        not any(
            token in combined_source
            for token in forbidden_storage_tokens
        ),
    ))

    tests.append((
        "PAB17 Teacher role remains distinct",
        teacher.role
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
            "RESULT: PASS - ADMIN PORTAL "
            "AUTHORIZATION BOUNDARY VERIFIED"
        )
        raise SystemExit(0)

    print(
        "RESULT: FAIL - ADMIN PORTAL "
        "AUTHORIZATION BOUNDARY VIOLATED"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
