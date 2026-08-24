from datetime import datetime, timezone
import inspect

from portal_v2.dashboard import (
    AdminDashboardActivity,
    AdminDashboardQueryService,
    AdminDashboardQuerySource,
    AdminDashboardReadModel,
    AdminDashboardStatusCounts,
)


class FakeDashboardSource(
    AdminDashboardQuerySource
):
    def __init__(
        self,
        *,
        counts,
        activity,
    ):
        self.counts = counts
        self.activity = activity
        self.last_limit = None

    def status_counts(
        self,
    ) -> AdminDashboardStatusCounts:
        return self.counts

    def recent_activity(
        self,
        *,
        limit: int,
    ) -> tuple[AdminDashboardActivity, ...]:
        self.last_limit = limit
        return self.activity[:limit]


class InvalidCountsSource(
    AdminDashboardQuerySource
):
    def status_counts(self):
        return "bad"

    def recent_activity(
        self,
        *,
        limit: int,
    ):
        return ()


class InvalidActivityContainerSource(
    AdminDashboardQuerySource
):
    def status_counts(self):
        return AdminDashboardStatusCounts(
            draft=0,
            pending=0,
            verified=0,
            published=0,
        )

    def recent_activity(
        self,
        *,
        limit: int,
    ):
        return []


class InvalidActivityItemSource(
    AdminDashboardQuerySource
):
    def status_counts(self):
        return AdminDashboardStatusCounts(
            draft=0,
            pending=0,
            verified=0,
            published=0,
        )

    def recent_activity(
        self,
        *,
        limit: int,
    ):
        return ("bad",)


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
        "WR-001E.2E.2 - "
        "ADMIN DASHBOARD QUERY SERVICE CONTRACT TEST"
    )
    print("=" * 72)

    now = datetime.now(timezone.utc)

    counts = AdminDashboardStatusCounts(
        draft=1,
        pending=2,
        verified=3,
        published=4,
    )

    activity = (
        AdminDashboardActivity(
            activity_id="ACT-1",
            record_id="REC-1",
            action="VERIFIED",
            actor_id="ADMIN-1",
            occurred_at=now,
            summary="Verified record.",
        ),
        AdminDashboardActivity(
            activity_id="ACT-2",
            record_id="REC-2",
            action="PUBLISHED",
            actor_id="ADMIN-2",
            occurred_at=now,
            summary="Published record.",
        ),
    )

    source = FakeDashboardSource(
        counts=counts,
        activity=activity,
    )

    service = AdminDashboardQueryService(
        source=source,
        clock=lambda: now,
    )

    model = service.build_read_model(
        activity_limit=1,
    )

    tests = []

    tests.append((
        "ADQS1 Query source contract is abstract",
        bool(
            getattr(
                AdminDashboardQuerySource,
                "__abstractmethods__",
                (),
            )
        ),
    ))

    tests.append((
        "ADQS2 Service accepted valid source",
        isinstance(
            service,
            AdminDashboardQueryService,
        ),
    ))

    tests.append((
        "ADQS3 Read model produced",
        isinstance(
            model,
            AdminDashboardReadModel,
        ),
    ))

    tests.append((
        "ADQS4 Status counts preserved",
        model.status_counts
        == counts,
    ))

    tests.append((
        "ADQS5 Activity limit forwarded",
        source.last_limit == 1,
    ))

    tests.append((
        "ADQS6 Activity limit applied",
        len(
            model.recent_activity
        )
        == 1,
    ))

    tests.append((
        "ADQS7 Clock timestamp preserved",
        model.generated_at == now,
    ))

    tests.append((
        "ADQS8 Invalid source blocked",
        expect_error(
            TypeError,
            lambda: AdminDashboardQueryService(
                source=object(),
                clock=lambda: now,
            ),
        ),
    ))

    tests.append((
        "ADQS9 Non-callable clock blocked",
        expect_error(
            TypeError,
            lambda: AdminDashboardQueryService(
                source=source,
                clock=None,
            ),
        ),
    ))

    tests.append((
        "ADQS10 Boolean activity limit blocked",
        expect_error(
            TypeError,
            lambda: service.build_read_model(
                activity_limit=True,
            ),
        ),
    ))

    tests.append((
        "ADQS11 Non-positive activity limit blocked",
        expect_error(
            ValueError,
            lambda: service.build_read_model(
                activity_limit=0,
            ),
        ),
    ))

    tests.append((
        "ADQS12 Invalid status count result blocked",
        expect_error(
            TypeError,
            lambda: AdminDashboardQueryService(
                source=InvalidCountsSource(),
                clock=lambda: now,
            ).build_read_model(),
        ),
    ))

    tests.append((
        "ADQS13 Non-tuple activity blocked",
        expect_error(
            TypeError,
            lambda: AdminDashboardQueryService(
                source=InvalidActivityContainerSource(),
                clock=lambda: now,
            ).build_read_model(),
        ),
    ))

    tests.append((
        "ADQS14 Invalid activity item blocked",
        expect_error(
            TypeError,
            lambda: AdminDashboardQueryService(
                source=InvalidActivityItemSource(),
                clock=lambda: now,
            ).build_read_model(),
        ),
    ))

    tests.append((
        "ADQS15 Invalid clock result blocked",
        expect_error(
            TypeError,
            lambda: AdminDashboardQueryService(
                source=source,
                clock=lambda: "now",
            ).build_read_model(),
        ),
    ))

    source_code = (
        inspect.getsource(
            AdminDashboardQueryService
        )
        + inspect.getsource(
            AdminDashboardQuerySource
        )
    )

    tests.append((
        "ADQS16 Service contains no Streamlit dependency",
        "streamlit" not in source_code.lower(),
    ))

    tests.append((
        "ADQS17 Service contains no Supabase dependency",
        all(
            token not in source_code.lower()
            for token in (
                "from supabase",
                "import supabase",
                ".table(",
                "create_client(",
            )
        ),
    ))

    tests.append((
        "ADQS18 Service contains no physical storage dependency",
        all(
            token not in source_code.lower()
            for token in (
                "sqlite",
                "postgres",
                "open(",
                "path(",
                "json.load",
            )
        ),
    ))

    tests.append((
        "ADQS19 Service contains no fixed educational values",
        all(
            token not in source_code
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
        "ADQS20 Service depends on query source contract",
        "AdminDashboardQuerySource"
        in inspect.getsource(
            AdminDashboardQueryService
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
            "RESULT: PASS - ADMIN DASHBOARD "
            "QUERY SERVICE CONTRACT VERIFIED"
        )
        raise SystemExit(0)

    print(
        "RESULT: FAIL - ADMIN DASHBOARD "
        "QUERY SERVICE CONTRACT VIOLATED"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
