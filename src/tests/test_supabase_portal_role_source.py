import inspect

from portal_v2.authorization import (
    PORTAL_ROLE_ADMIN,
    PORTAL_ROLE_TEACHER,
    SupabaseTrustedPortalRoleSource,
    TrustedPortalRoleSource,
)


class FakeResponse:
    def __init__(
        self,
        data,
    ):
        self.data = data


class FakeQuery:
    def __init__(
        self,
        response,
    ):
        self.response = response
        self.filters = []
        self.selected = None
        self.limit_value = None

    def select(
        self,
        value,
    ):
        self.selected = value
        return self

    def eq(
        self,
        key,
        value,
    ):
        self.filters.append(
            (
                key,
                value,
            )
        )
        return self

    def limit(
        self,
        value,
    ):
        self.limit_value = value
        return self

    def execute(self):
        if isinstance(
            self.response,
            Exception,
        ):
            raise self.response

        return FakeResponse(
            self.response
        )


class FakeClient:
    def __init__(
        self,
        response,
    ):
        self.response = response
        self.table_name = None
        self.query = None

    def table(
        self,
        table_name,
    ):
        self.table_name = table_name
        self.query = FakeQuery(
            self.response
        )
        return self.query


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
        "WR-001E.2D.3C - "
        "SUPABASE TRUSTED PORTAL ROLE SOURCE TEST"
    )
    print("=" * 72)

    tests = []

    admin_client = FakeClient([
        {
            "user_id": "USER-ADMIN",
            "role": "admin",
        }
    ])

    admin_source = (
        SupabaseTrustedPortalRoleSource(
            client=admin_client
        )
    )

    admin_result = (
        admin_source.resolve_role(
            user_id="USER-ADMIN"
        )
    )

    tests.append((
        "SPRSA1 Adapter implements trusted role source",
        isinstance(
            admin_source,
            TrustedPortalRoleSource,
        ),
    ))

    tests.append((
        "SPRSA2 Dedicated role table used",
        admin_client.table_name
        == "portal_roles",
    ))

    tests.append((
        "SPRSA3 Query selects role by user ID",
        admin_client.query.filters
        == [
            (
                "user_id",
                "USER-ADMIN",
            )
        ],
    ))

    tests.append((
        "SPRSA4 Query limited to one record",
        admin_client.query.limit_value
        == 1,
    ))

    tests.append((
        "SPRSA5 Trusted admin resolved",
        (
            admin_result.role
            == PORTAL_ROLE_ADMIN
            and
            admin_result.trusted
            is True
            and
            admin_result.effective_role
            == PORTAL_ROLE_ADMIN
        ),
    ))

    teacher_client = FakeClient([
        {
            "user_id": "USER-TEACHER",
            "role": "teacher",
        }
    ])

    teacher_result = (
        SupabaseTrustedPortalRoleSource(
            client=teacher_client
        )
        .resolve_role(
            user_id="USER-TEACHER"
        )
    )

    tests.append((
        "SPRSA6 Trusted teacher resolved",
        (
            teacher_result.role
            == PORTAL_ROLE_TEACHER
            and
            teacher_result.trusted
            is True
        ),
    ))

    missing_result = (
        SupabaseTrustedPortalRoleSource(
            client=FakeClient([])
        )
        .resolve_role(
            user_id="USER-MISSING"
        )
    )

    tests.append((
        "SPRSA7 Missing role fails safe to teacher",
        (
            missing_result.effective_role
            == PORTAL_ROLE_TEACHER
            and
            missing_result.trusted
            is False
        ),
    ))

    malformed_result = (
        SupabaseTrustedPortalRoleSource(
            client=FakeClient([
                {
                    "user_id": "USER-X",
                    "role": "owner",
                }
            ])
        )
        .resolve_role(
            user_id="USER-X"
        )
    )

    tests.append((
        "SPRSA8 Unsupported role fails safe",
        (
            malformed_result.effective_role
            == PORTAL_ROLE_TEACHER
            and
            malformed_result.trusted
            is False
        ),
    ))

    mismatch_result = (
        SupabaseTrustedPortalRoleSource(
            client=FakeClient([
                {
                    "user_id": "OTHER-USER",
                    "role": "admin",
                }
            ])
        )
        .resolve_role(
            user_id="USER-X"
        )
    )

    tests.append((
        "SPRSA9 User identity mismatch fails safe",
        mismatch_result.effective_role
        == PORTAL_ROLE_TEACHER,
    ))

    failure_result = (
        SupabaseTrustedPortalRoleSource(
            client=FakeClient(
                RuntimeError(
                    "network failure"
                )
            )
        )
        .resolve_role(
            user_id="USER-X"
        )
    )

    tests.append((
        "SPRSA10 Source failure fails safe",
        (
            failure_result.effective_role
            == PORTAL_ROLE_TEACHER
            and
            failure_result.trusted
            is False
        ),
    ))

    tests.append((
        "SPRSA11 Empty user ID blocked",
        expect_error(
            ValueError,
            lambda: admin_source.resolve_role(
                user_id=" "
            ),
        ),
    ))

    tests.append((
        "SPRSA12 Wrong user ID type blocked",
        expect_error(
            TypeError,
            lambda: admin_source.resolve_role(
                user_id=123
            ),
        ),
    ))

    tests.append((
        "SPRSA13 Missing client blocked",
        expect_error(
            ValueError,
            lambda: SupabaseTrustedPortalRoleSource(
                client=None
            ),
        ),
    ))

    source = inspect.getsource(
        SupabaseTrustedPortalRoleSource
    )

    tests.append((
        "SPRSA14 Adapter does not use email authorization",
        all(
            token not in source.lower()
            for token in (
                "email ==",
                "email.endswith",
                "admin@",
            )
        ),
    ))

    tests.append((
        "SPRSA15 Adapter does not use user metadata for role",
        all(
            token not in source.lower()
            for token in (
                "user_metadata",
                "raw_user_meta_data",
            )
        ),
    ))

    tests.append((
        "SPRSA16 Adapter contains no educational values",
        all(
            token not in source
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
            "RESULT: PASS - SUPABASE TRUSTED "
            "PORTAL ROLE SOURCE VERIFIED"
        )
        raise SystemExit(0)

    print(
        "RESULT: FAIL - SUPABASE TRUSTED "
        "PORTAL ROLE SOURCE VIOLATED"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
