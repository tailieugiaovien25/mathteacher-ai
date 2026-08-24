from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from curriculum_v2.governance.in_memory_trusted_admin_data_repository import (
    InMemoryTrustedAdministrativeDataRepository,
)
from portal_v2.dashboard.admin_dashboard_query_service import (
    AdminDashboardQuerySource,
)
from portal_v2.dashboard.trusted_admin_repository_dashboard_query_source import (
    TrustedAdminRepositoryDashboardQuerySource,
)


class TestState(Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    PUBLISHED = "PUBLISHED"
    FUTURE = "FUTURE"


@dataclass(frozen=True)
class TestAuditEvent:
    event_id: str
    action: str
    actor_id: str
    occurred_at: datetime
    summary: str


@dataclass(frozen=True)
class TestAdministrativeSubmission:
    submission_id: str
    state: TestState
    audit_trail: tuple[TestAuditEvent, ...]


def report(
    label: str,
    condition: bool,
) -> bool:
    print(
        f"{label}: "
        f"{'PASS' if condition else 'FAIL'}"
    )
    return condition


def save_submission(
    repository,
    submission,
) -> None:
    repository.save(
        record_id=submission.submission_id,
        record=submission,
    )


def main() -> int:
    print("=" * 72)
    print(
        "WR-001E.2E.3B - TRUSTED ADMIN REPOSITORY "
        "DASHBOARD QUERY SOURCE TEST"
    )
    print("=" * 72)

    checks = []

    repository = (
        InMemoryTrustedAdministrativeDataRepository()
    )

    source = (
        TrustedAdminRepositoryDashboardQuerySource(
            repository=repository
        )
    )

    checks.append(report(
        "TARDQS1 Adapter implements dashboard query source",
        isinstance(
            source,
            AdminDashboardQuerySource,
        ),
    ))

    for submission in (
        TestAdministrativeSubmission(
            "record-draft",
            TestState.DRAFT,
            (),
        ),
        TestAdministrativeSubmission(
            "record-pending",
            TestState.PENDING,
            (),
        ),
        TestAdministrativeSubmission(
            "record-verified",
            TestState.VERIFIED,
            (),
        ),
        TestAdministrativeSubmission(
            "record-published",
            TestState.PUBLISHED,
            (),
        ),
        TestAdministrativeSubmission(
            "record-future",
            TestState.FUTURE,
            (),
        ),
    ):
        save_submission(
            repository,
            submission,
        )

    counts = source.status_counts()

    checks.append(report(
        "TARDQS2 Draft count aggregated",
        counts.draft == 1,
    ))
    checks.append(report(
        "TARDQS3 Pending count aggregated",
        counts.pending == 1,
    ))
    checks.append(report(
        "TARDQS4 Verified count aggregated",
        counts.verified == 1,
    ))
    checks.append(report(
        "TARDQS5 Published count aggregated",
        counts.published == 1,
    ))
    checks.append(report(
        "TARDQS6 Unknown status ignored safely",
        counts.total == 4,
    ))

    repository = (
        InMemoryTrustedAdministrativeDataRepository()
    )

    source = (
        TrustedAdminRepositoryDashboardQuerySource(
            repository=repository
        )
    )

    older = datetime(
        2026,
        8,
        15,
        8,
        0,
        tzinfo=timezone.utc,
    )

    newer = datetime(
        2026,
        8,
        15,
        9,
        0,
        tzinfo=timezone.utc,
    )

    save_submission(
        repository,
        TestAdministrativeSubmission(
            submission_id="record-a",
            state=TestState.VERIFIED,
            audit_trail=(
                TestAuditEvent(
                    event_id="event-old",
                    action="SUBMITTED",
                    actor_id="actor-a",
                    occurred_at=older,
                    summary="Submitted for review",
                ),
                TestAuditEvent(
                    event_id="event-new",
                    action="VERIFIED",
                    actor_id="actor-b",
                    occurred_at=newer,
                    summary="Verified by administrator",
                ),
            ),
        ),
    )

    activities = source.recent_activity(
        limit=1
    )

    checks.append(report(
        "TARDQS7 Activity limit applied",
        len(activities) == 1,
    ))
    checks.append(report(
        "TARDQS8 Recent activity sorted newest first",
        activities[0].activity_id
        == "event-new",
    ))
    checks.append(report(
        "TARDQS9 Activity record identity preserved",
        activities[0].record_id
        == "record-a",
    ))
    checks.append(report(
        "TARDQS10 Activity actor preserved",
        activities[0].actor_id
        == "actor-b",
    ))
    checks.append(report(
        "TARDQS11 Activity timestamp preserved",
        activities[0].occurred_at
        == newer,
    ))

    try:
        source.recent_activity(
            limit=True
        )
        bool_limit_blocked = False
    except TypeError:
        bool_limit_blocked = True

    checks.append(report(
        "TARDQS12 Boolean activity limit blocked",
        bool_limit_blocked,
    ))

    try:
        source.recent_activity(
            limit=0
        )
        non_positive_blocked = False
    except ValueError:
        non_positive_blocked = True

    checks.append(report(
        "TARDQS13 Non-positive activity limit blocked",
        non_positive_blocked,
    ))

    try:
        TrustedAdminRepositoryDashboardQuerySource(
            repository=object()
        )
        bad_repository_blocked = False
    except TypeError:
        bad_repository_blocked = True

    checks.append(report(
        "TARDQS14 Invalid repository blocked",
        bad_repository_blocked,
    ))

    source_text = Path(
        "src/portal_v2/dashboard/"
        "trusted_admin_repository_dashboard_query_source.py"
    ).read_text(
        encoding="utf-8"
    ).lower()

    checks.append(report(
        "TARDQS15 Adapter contains no Streamlit dependency",
        "streamlit"
        not in source_text,
    ))

    checks.append(report(
        "TARDQS16 Adapter contains no Supabase dependency",
        "supabase"
        not in source_text,
    ))

    checks.append(report(
        "TARDQS17 Adapter contains no SQLite dependency",
        "sqlite"
        not in source_text,
    ))

    checks.append(report(
        "TARDQS18 Adapter contains no physical path dependency",
        (
            "database_path"
            not in source_text
            and ".db"
            not in source_text
        ),
    ))

    checks.append(report(
        "TARDQS19 Adapter contains no fixed educational values",
        all(
            token not in source_text
            for token in (
                "toán 6",
                "kết nối tri thức",
                "140",
                "105",
                "70",
                "35",
            )
        ),
    ))

    checks.append(report(
        "TARDQS20 Future record type needs no adapter change",
        "testadministrativesubmission"
        not in source_text,
    ))

    if all(checks):
        print()
        print(
            "RESULT: PASS - TRUSTED ADMIN REPOSITORY "
            "DASHBOARD QUERY SOURCE VERIFIED"
        )
        return 0

    print()
    print(
        "RESULT: FAIL - TRUSTED ADMIN REPOSITORY "
        "DASHBOARD QUERY SOURCE VIOLATED"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
