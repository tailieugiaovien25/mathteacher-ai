from datetime import datetime, timezone

from curriculum_v2.authority import (
    CanonicalCurriculumAuthoritySource,
)
from curriculum_v2.canonical_curriculum import (
    CanonicalCurriculumFacade,
)
from curriculum_v2.governance import (
    AdministrativeDataWorkflow,
    AdministrativeTimeAllocationPayload,
    AdministrativeTimeAllocationPublicationBridge,
    AdministrativeVerificationPolicy,
    DataTrustLevel,
    GovernanceActor,
    GovernancePermission,
)
from curriculum_v2.providers import (
    CapabilityEducationalDataProvider,
)
from curriculum_v2.providers.contracts import (
    EducationalDataProvenance,
    EducationalDataQuery,
    EducationalDataResult,
    EducationalDataVersion,
)


class FakeCanonicalCurriculumFacade(
    CanonicalCurriculumFacade
):
    def __init__(self):
        pass

    def requirements_for_grade(
        self,
        grade,
    ):
        return ()

    def requirement_by_id(
        self,
        canonical_id,
    ):
        return None

    def nodes_for_grade(
        self,
        grade,
    ):
        return ()

    def node_by_id(
        self,
        curriculum_node_id,
    ):
        return None


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


def build_published_allocation(
    *,
    total_periods: int,
    allocation_id: str,
    submission_id: str,
):
    now = datetime.now(
        timezone.utc
    )

    entry = GovernanceActor(
        actor_id="ENTRY-ADMIN",
        permissions=(
            GovernancePermission.ENTER_DATA,
        ),
    )

    verifier = GovernanceActor(
        actor_id="VERIFY-ADMIN",
        permissions=(
            GovernancePermission.VERIFY_DATA,
        ),
    )

    publisher = GovernanceActor(
        actor_id="PUBLISH-ADMIN",
        permissions=(
            GovernancePermission.PUBLISH_DATA,
        ),
    )

    draft = AdministrativeDataWorkflow.create_draft(
        submission_id=submission_id,
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
            source_reference="ADMIN-SOURCE-REF",
        )
    )

    payload = AdministrativeTimeAllocationPayload(
        allocation_id=allocation_id,
        curriculum_ref="CURR-A",
        subject_ref="SUBJECT-A",
        grade=6,
        total_periods=total_periods,
        legal_authority="ADMIN-AUTHORITY",
        regulation_id="ADMIN-REGULATION",
        source_document_id="ADMIN-SOURCE",
        source_location="ADMIN-SECTION",
        source_version="V1",
    )

    published_result = (
        AdministrativeTimeAllocationPublicationBridge
        .publish(
            payload=payload,
            submission=published,
            verification=verification,
        )
    )

    return (
        published_result,
        draft,
        pending,
        verified,
        verification,
        payload,
    )


def make_provider(
    canonical_allocation,
):
    authority = CanonicalCurriculumAuthoritySource(
        facade=FakeCanonicalCurriculumFacade(),
        curriculum_refs=(
            "CURR-A",
        ),
        subject_refs=(
            "SUBJECT-A",
        ),
        time_allocations=(
            canonical_allocation,
        ),
    )

    def time_allocation_handler(
        query: EducationalDataQuery,
    ) -> EducationalDataResult:
        allocation = authority.time_allocation(
            curriculum_ref=query.curriculum_ref,
            subject_ref=query.subject_ref,
            grade=int(query.grade_ref),
        )

        data = (
            ()
            if allocation is None
            else (allocation,)
        )

        return EducationalDataResult(
            capability=query.capability,
            data=data,
            provenance=EducationalDataProvenance(
                source_id="ADMIN-TRUSTED-DATA",
                authority_type="ADMIN_VERIFIED",
                source_version="V1",
                status="VERIFIED",
            ),
            version=EducationalDataVersion(
                version_id="V1",
            ),
        )

    return CapabilityEducationalDataProvider(
        handlers={
            "time_allocation":
                time_allocation_handler,
        }
    )


def main():
    print("=" * 76)
    print(
        "WR-001D.12C.5C.6 - TRUSTED ADMIN "
        "TIME ALLOCATION END-TO-END TEST"
    )
    print("=" * 76)

    results = []

    (
        published_result,
        draft,
        pending,
        verified,
        verification,
        payload,
    ) = build_published_allocation(
        total_periods=123,
        allocation_id="ALLOC-E2E-A",
        submission_id="SUB-E2E-A",
    )

    canonical = (
        published_result
        .canonical_allocation
    )

    provider = make_provider(
        canonical
    )

    query_result = provider.query(
        EducationalDataQuery(
            capability="time_allocation",
            curriculum_ref="CURR-A",
            subject_ref="SUBJECT-A",
            grade_ref="6",
        )
    )

    checks = [
        (
            "E2E1 Published admin data became canonical",
            canonical.total_periods == 123,
        ),
        (
            "E2E2 Governance record is ADMIN_VERIFIED",
            (
                published_result
                .governance_record
                .trust_level
                is DataTrustLevel.ADMIN_VERIFIED
            ),
        ),
        (
            "E2E3 Authority source accepted canonical record",
            len(query_result.data) == 1,
        ),
        (
            "E2E4 Provider returned trusted value",
            query_result.data[0].total_periods
            == 123,
        ),
        (
            "E2E5 Provider capability preserved",
            query_result.capability
            == "time_allocation",
        ),
        (
            "E2E6 Provider provenance is verified",
            query_result.provenance.status
            == "VERIFIED",
        ),
        (
            "E2E7 Canonical provenance preserved",
            (
                query_result.data[0]
                .provenance
                .source_document_id
                == "ADMIN-SOURCE"
            ),
        ),
        (
            "E2E8 Admin entry identity traceable",
            (
                published_result
                .governance_record
                .administrative_verification
                .entered_by
                == "ENTRY-ADMIN"
            ),
        ),
        (
            "E2E9 Admin verifier identity traceable",
            (
                published_result
                .governance_record
                .administrative_verification
                .verified_by
                == "VERIFY-ADMIN"
            ),
        ),
        (
            "E2E10 Submission version traceable",
            (
                published_result
                .governance_record
                .metadata["submission_version"]
                == str(
                    published_result
                    .submission
                    .version
                )
            ),
        ),
    ]

    checks.append(
        (
            "E2E11 Draft cannot enter canonical pipeline",
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
        )
    )

    checks.append(
        (
            "E2E12 Pending cannot enter canonical pipeline",
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
        )
    )

    checks.append(
        (
            "E2E13 Verified-but-unpublished cannot enter pipeline",
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
        )
    )

    (
        changed_published_result,
        _,
        _,
        _,
        _,
        _,
    ) = build_published_allocation(
        total_periods=321,
        allocation_id="ALLOC-E2E-B",
        submission_id="SUB-E2E-B",
    )

    changed_provider = make_provider(
        changed_published_result
        .canonical_allocation
    )

    changed_query_result = (
        changed_provider.query(
            EducationalDataQuery(
                capability="time_allocation",
                curriculum_ref="CURR-A",
                subject_ref="SUBJECT-A",
                grade_ref="6",
            )
        )
    )

    checks.append(
        (
            "E2E14 Changed trusted data needs no code change",
            changed_query_result.data[0].total_periods
            == 321,
        )
    )

    missing_result = provider.query(
        EducationalDataQuery(
            capability="time_allocation",
            curriculum_ref="CURR-A",
            subject_ref="SUBJECT-A",
            grade_ref="7",
        )
    )

    checks.append(
        (
            "E2E15 Missing allocation returns empty data",
            missing_result.data == (),
        )
    )

    checks.append(
        (
            "E2E16 Provider owns no concrete period rule",
            (
                provider.capabilities
                == ("time_allocation",)
            ),
        )
    )

    for label, passed in checks:
        results.append(
            passed
        )

        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print()
    print("END-TO-END SUMMARY")
    print(
        "INPUT VALUE            :",
        123,
    )
    print(
        "CANONICAL VALUE        :",
        canonical.total_periods,
    )
    print(
        "PROVIDER VALUE         :",
        query_result.data[0].total_periods,
    )
    print(
        "TRUST LEVEL            :",
        (
            published_result
            .governance_record
            .trust_level
            .value
        ),
    )
    print(
        "SUBMISSION STATE       :",
        (
            published_result
            .submission
            .state
            .value
        ),
    )
    print(
        "SUBMISSION VERSION     :",
        published_result.submission.version,
    )
    print(
        "AUDIT EVENTS           :",
        len(
            published_result
            .submission
            .audit_trail
        ),
    )
    print()

    if all(results):
        print(
            "RESULT: PASS - TRUSTED ADMIN "
            "TIME ALLOCATION END-TO-END VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - TRUSTED ADMIN "
            "TIME ALLOCATION END-TO-END VIOLATED"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
