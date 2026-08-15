from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import inspect

from portal_v2.dashboard import (
    DASHBOARD_STATUSES,
    AdminDashboardActivity,
    AdminDashboardReadModel,
    AdminDashboardStatusCounts,
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
        "WR-001E.2E.1 - "
        "ADMIN DASHBOARD READ MODEL CONTRACT TEST"
    )
    print("=" * 72)

    now = datetime.now(timezone.utc)

    counts = AdminDashboardStatusCounts(
        draft=2,
        pending=3,
        verified=4,
        published=5,
    )

    activity = AdminDashboardActivity(
        activity_id="ACT-001",
        record_id="REC-001",
        action="PUBLISHED",
        actor_id="ADMIN-001",
        occurred_at=now,
        summary="Published trusted administrative data.",
    )

    model = AdminDashboardReadModel(
        status_counts=counts,
        recent_activity=(activity,),
        generated_at=now,
    )

    tests = []

    tests.append((
        "ADR1 Status counts accepted",
        counts.total == 14,
    ))

    tests.append((
        "ADR2 Dashboard statuses locked",
        DASHBOARD_STATUSES
        == (
            "DRAFT",
            "PENDING",
            "VERIFIED",
            "PUBLISHED",
        ),
    ))

    tests.append((
        "ADR3 Activity accepted",
        activity.action == "PUBLISHED",
    ))

    tests.append((
        "ADR4 Read model accepted",
        model.status_counts.published == 5,
    ))

    tests.append((
        "ADR5 Activity tuple preserved",
        isinstance(
            model.recent_activity,
            tuple,
        ),
    ))

    tests.append((
        "ADR6 Negative count blocked",
        expect_error(
            ValueError,
            lambda: AdminDashboardStatusCounts(
                draft=-1,
                pending=0,
                verified=0,
                published=0,
            ),
        ),
    ))

    tests.append((
        "ADR7 Boolean count blocked",
        expect_error(
            TypeError,
            lambda: AdminDashboardStatusCounts(
                draft=True,
                pending=0,
                verified=0,
                published=0,
            ),
        ),
    ))

    tests.append((
        "ADR8 Empty activity ID blocked",
        expect_error(
            ValueError,
            lambda: AdminDashboardActivity(
                activity_id=" ",
                record_id="REC",
                action="PUBLISHED",
                actor_id="ADMIN",
                occurred_at=now,
                summary="Summary",
            ),
        ),
    ))

    tests.append((
        "ADR9 Invalid activity time blocked",
        expect_error(
            TypeError,
            lambda: AdminDashboardActivity(
                activity_id="ACT",
                record_id="REC",
                action="PUBLISHED",
                actor_id="ADMIN",
                occurred_at="now",
                summary="Summary",
            ),
        ),
    ))

    tests.append((
        "ADR10 Non-tuple activity blocked",
        expect_error(
            TypeError,
            lambda: AdminDashboardReadModel(
                status_counts=counts,
                recent_activity=[activity],
                generated_at=now,
            ),
        ),
    ))

    tests.append((
        "ADR11 Invalid activity item blocked",
        expect_error(
            TypeError,
            lambda: AdminDashboardReadModel(
                status_counts=counts,
                recent_activity=("bad",),
                generated_at=now,
            ),
        ),
    ))

    tests.append((
        "ADR12 Read model immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                model,
                "generated_at",
                now,
            ),
        ),
    ))

    tests.append((
        "ADR13 Status counts immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                counts,
                "draft",
                99,
            ),
        ),
    ))

    tests.append((
        "ADR14 Activity immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                activity,
                "action",
                "CHANGED",
            ),
        ),
    ))

    source = (
        inspect.getsource(
            AdminDashboardReadModel
        )
        + inspect.getsource(
            AdminDashboardStatusCounts
        )
        + inspect.getsource(
            AdminDashboardActivity
        )
    )

    tests.append((
        "ADR15 Read model contains no Streamlit dependency",
        "streamlit" not in source.lower(),
    ))

    tests.append((
        "ADR16 Read model contains no Supabase dependency",
        all(
            token not in source.lower()
            for token in (
                "from supabase",
                "import supabase",
                ".table(",
                "create_client(",
            )
        ),
    ))

    tests.append((
        "ADR17 Read model contains no physical storage dependency",
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

    tests.append((
        "ADR18 Read model contains no fixed educational values",
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

    tests.append((
        "ADR19 Dashboard read model owns no repository",
        "repository" not in source.lower(),
    ))

    tests.append((
        "ADR20 Generated timestamp preserved",
        model.generated_at == now,
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
            "READ MODEL CONTRACT VERIFIED"
        )
        raise SystemExit(0)

    print(
        "RESULT: FAIL - ADMIN DASHBOARD "
        "READ MODEL CONTRACT VIOLATED"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
