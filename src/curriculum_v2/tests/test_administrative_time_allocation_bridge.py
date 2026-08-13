import inspect

from datetime import datetime, timezone

from curriculum_v2.governance import (
    AdministrativeDataWorkflow,
    AdministrativeTimeAllocationPayload,
    AdministrativeTimeAllocationPublicationBridge,
    AdministrativeVerificationPolicy,
    DataTrustLevel,
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
        "WR-001D.12C.5C.5 - ADMIN TIME "
        "ALLOCATION PUBLICATION BRIDGE TEST"
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

    draft = AdministrativeDataWorkflow.create_draft(
        submission_id="SUB-TA-001",
        actor=entry,
    )

    pending = AdministrativeDataWorkflow.submit(
        submission=draft,
        actor=entry,
        occurred_at=now,
    )

    verified = AdministrativeDataWorkflow.verify(
        submission=pending,
        actor=verifier,
        occurred_at=now,
    )

    published = AdministrativeDataWorkflow.publish(
        submission=verified,
        actor=publisher,
        occurred_at=now,
    )

    verification = (
        AdministrativeVerificationPolicy
        .create_verification(
            entered_by=entry.actor_id,
            verifier=verifier,
            verified_at=now,
            source_reference="SECONDARY-SOURCE-A",
        )
    )

    payload = AdministrativeTimeAllocationPayload(
        allocation_id="ALLOC-A",
        curriculum_ref="CURR-A",
        subject_ref="SUBJECT-A",
        grade=6,
        total_periods=123,
        legal_authority="AUTHORITY",
        regulation_id="REGULATION",
        source_document_id="SOURCE",
        source_location="SECTION",
        source_version="V1",
    )

    result = (
        AdministrativeTimeAllocationPublicationBridge
        .publish(
            payload=payload,
            submission=published,
            verification=verification,
        )
    )

    tests = []

    tests.append((
        "ATPB1 Published submission accepted",
        result.submission is published,
    ))

    tests.append((
        "ATPB2 Canonical allocation produced",
        result.canonical_allocation.allocation_id
        == "ALLOC-A",
    ))

    tests.append((
        "ATPB3 Administrative value preserved",
        result.canonical_allocation.total_periods
        == 123,
    ))

    tests.append((
        "ATPB4 Canonical status verified",
        result.canonical_allocation.status
        == "VERIFIED",
    ))

    tests.append((
        "ATPB5 Governance trust preserved",
        result.governance_record.trust_level
        is DataTrustLevel.ADMIN_VERIFIED,
    ))

    tests.append((
        "ATPB6 Entered-by preserved",
        (
            result.governance_record
            .administrative_verification
            .entered_by
        )
        == "ENTRY",
    ))

    tests.append((
        "ATPB7 Verified-by preserved",
        (
            result.governance_record
            .administrative_verification
            .verified_by
        )
        == "VERIFIER",
    ))

    tests.append((
        "ATPB8 Source reference preserved",
        (
            result.governance_record
            .administrative_verification
            .source_reference
        )
        == "SECONDARY-SOURCE-A",
    ))

    tests.append((
        "ATPB9 Submission version preserved",
        (
            result.governance_record
            .metadata["submission_version"]
        )
        == str(published.version),
    ))

    tests.append((
        "ATPB10 Audit trail count preserved",
        (
            result.governance_record
            .metadata["audit_event_count"]
        )
        == str(len(published.audit_trail)),
    ))

    tests.append((
        "ATPB11 Draft cannot publish canonical data",
        expect_error(
            ValueError,
            lambda: (
                AdministrativeTimeAllocationPublicationBridge
                .publish(
                    payload=payload,
                    submission=draft,
                    verification=verification,
                )
            ),
        ),
    ))

    tests.append((
        "ATPB12 Pending cannot publish canonical data",
        expect_error(
            ValueError,
            lambda: (
                AdministrativeTimeAllocationPublicationBridge
                .publish(
                    payload=payload,
                    submission=pending,
                    verification=verification,
                )
            ),
        ),
    ))

    tests.append((
        "ATPB13 Verified-but-unpublished blocked",
        expect_error(
            ValueError,
            lambda: (
                AdministrativeTimeAllocationPublicationBridge
                .publish(
                    payload=payload,
                    submission=verified,
                    verification=verification,
                )
            ),
        ),
    ))

    changed_payload = (
        AdministrativeTimeAllocationPayload(
            allocation_id="ALLOC-B",
            curriculum_ref="CURR-A",
            subject_ref="SUBJECT-A",
            grade=6,
            total_periods=321,
            legal_authority="AUTHORITY",
            regulation_id="REGULATION",
            source_document_id="SOURCE",
        )
    )

    changed_result = (
        AdministrativeTimeAllocationPublicationBridge
        .publish(
            payload=changed_payload,
            submission=published,
            verification=verification,
        )
    )

    tests.append((
        "ATPB14 Different trusted value needs no code change",
        changed_result.canonical_allocation.total_periods
        == 321,
    ))

    tests.append((
        "ATPB15 Provenance preserved",
        (
            result.canonical_allocation
            .provenance
            .source_document_id
        )
        == "SOURCE",
    ))

    bridge_source = inspect.getsource(
        AdministrativeTimeAllocationPublicationBridge
    )

    forbidden_educational_values = (
        "140",
        "105",
        "70",
        "35",
        "KNTT",
        "Toán 6",
    )

    tests.append((
        "ATPB16 Bridge contains no fixed educational values",
        not any(
            token in bridge_source
            for token in forbidden_educational_values
        ),
    ))

    passed = True

    for label, value in tests:
        print(
            f"{label}: "
            f"{'PASS' if value else 'FAIL'}"
        )

        passed = passed and value

    print()

    if passed:
        print(
            "RESULT: PASS - ADMIN TIME ALLOCATION "
            "PUBLICATION BRIDGE VERIFIED"
        )
        raise SystemExit(0)

    print(
        "RESULT: FAIL - ADMIN TIME ALLOCATION "
        "PUBLICATION BRIDGE VIOLATED"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
