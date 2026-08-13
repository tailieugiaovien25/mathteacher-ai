from datetime import datetime, timezone

from curriculum_v2.governance import (
    AdministrativeDataState,
    AdministrativeDataWorkflow,
    GovernanceActor,
    GovernancePermission,
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
        "WR-001D.12C.5C.4 - ADMINISTRATIVE "
        "TRUSTED DATA WORKFLOW TEST"
    )
    print("=" * 72)

    now = datetime.now(
        timezone.utc
    )

    entry = GovernanceActor(
        actor_id="ENTRY",
        permissions=(
            GovernancePermission.ENTER_DATA,
        ),
    )

    verifier = GovernanceActor(
        actor_id="VERIFIER",
        permissions=(
            GovernancePermission.VERIFY_DATA,
        ),
    )

    publisher = GovernanceActor(
        actor_id="PUBLISHER",
        permissions=(
            GovernancePermission.PUBLISH_DATA,
        ),
    )

    superseder = GovernanceActor(
        actor_id="SUPERSEDER",
        permissions=(
            GovernancePermission.SUPERSEDE_DATA,
        ),
    )

    tests = []

    draft = AdministrativeDataWorkflow.create_draft(
        submission_id="SUB-001",
        actor=entry,
    )

    tests.append((
        "ATW1 Draft created",
        draft.state is AdministrativeDataState.DRAFT,
    ))

    tests.append((
        "ATW2 Entry identity preserved",
        draft.entered_by == "ENTRY",
    ))

    pending = AdministrativeDataWorkflow.submit(
        submission=draft,
        actor=entry,
        occurred_at=now,
    )

    tests.append((
        "ATW3 Draft submitted to pending",
        pending.state is AdministrativeDataState.PENDING,
    ))

    verified = AdministrativeDataWorkflow.verify(
        submission=pending,
        actor=verifier,
        occurred_at=now,
    )

    tests.append((
        "ATW4 Pending verified",
        verified.state is AdministrativeDataState.VERIFIED,
    ))

    published = AdministrativeDataWorkflow.publish(
        submission=verified,
        actor=publisher,
        occurred_at=now,
    )

    tests.append((
        "ATW5 Verified data published",
        published.state is AdministrativeDataState.PUBLISHED,
    ))

    superseded = AdministrativeDataWorkflow.supersede(
        submission=published,
        actor=superseder,
        occurred_at=now,
    )

    tests.append((
        "ATW6 Published data superseded",
        superseded.state is AdministrativeDataState.SUPERSEDED,
    ))

    tests.append((
        "ATW7 Version increments",
        (
            draft.version == 1
            and pending.version == 2
            and verified.version == 3
            and published.version == 4
            and superseded.version == 5
        ),
    ))

    tests.append((
        "ATW8 Audit trail complete",
        len(
            superseded.audit_trail
        ) == 4,
    ))

    tests.append((
        "ATW9 Audit actors preserved",
        tuple(
            event.actor_id
            for event in superseded.audit_trail
        )
        == (
            "ENTRY",
            "VERIFIER",
            "PUBLISHER",
            "SUPERSEDER",
        ),
    ))

    tests.append((
        "ATW10 Unauthorized verify blocked",
        expect_error(
            PermissionError,
            lambda: AdministrativeDataWorkflow.verify(
                submission=pending,
                actor=entry,
                occurred_at=now,
            ),
        ),
    ))

    tests.append((
        "ATW11 Publish before verify blocked",
        expect_error(
            ValueError,
            lambda: AdministrativeDataWorkflow.publish(
                submission=pending,
                actor=publisher,
                occurred_at=now,
            ),
        ),
    ))

    tests.append((
        "ATW12 Verify draft blocked",
        expect_error(
            ValueError,
            lambda: AdministrativeDataWorkflow.verify(
                submission=draft,
                actor=verifier,
                occurred_at=now,
            ),
        ),
    ))

    tests.append((
        "ATW13 Supersede unpublished blocked",
        expect_error(
            ValueError,
            lambda: AdministrativeDataWorkflow.supersede(
                submission=verified,
                actor=superseder,
                occurred_at=now,
            ),
        ),
    ))

    tests.append((
        "ATW14 Original submissions immutable by transition",
        (
            draft.state is AdministrativeDataState.DRAFT
            and pending.state is AdministrativeDataState.PENDING
        ),
    ))

    tests.append((
        "ATW15 Audit transition sequence valid",
        tuple(
            (
                event.from_state,
                event.to_state,
            )
            for event in superseded.audit_trail
        )
        == (
            (
                AdministrativeDataState.DRAFT,
                AdministrativeDataState.PENDING,
            ),
            (
                AdministrativeDataState.PENDING,
                AdministrativeDataState.VERIFIED,
            ),
            (
                AdministrativeDataState.VERIFIED,
                AdministrativeDataState.PUBLISHED,
            ),
            (
                AdministrativeDataState.PUBLISHED,
                AdministrativeDataState.SUPERSEDED,
            ),
        ),
    ))

    tests.append((
        "ATW16 Workflow independent of educational values",
        all(
            token not in repr(
                AdministrativeDataWorkflow.__dict__
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

    passed = True

    for label, result in tests:
        print(
            f"{label}: "
            f"{'PASS' if result else 'FAIL'}"
        )

        passed = passed and result

    print()

    if passed:
        print(
            "RESULT: PASS - ADMINISTRATIVE "
            "TRUSTED DATA WORKFLOW VERIFIED"
        )
        raise SystemExit(0)

    print(
        "RESULT: FAIL - ADMINISTRATIVE "
        "TRUSTED DATA WORKFLOW VIOLATED"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
