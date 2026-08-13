from curriculum_v2.authority import (
    CanonicalCurriculumAuthoritySource,
)
from curriculum_v2.canonical_curriculum import (
    CanonicalCurriculumFacade,
)
from curriculum_v2.models.canonical_time_allocation import (
    CanonicalTimeAllocation,
    TimeAllocationProvenance,
)


class FakeFacade(
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


def make_allocation(
    *,
    allocation_id="ALLOC-A",
    curriculum_ref="CURR-A",
    subject_ref="SUBJECT-A",
    grade=6,
    total_periods=123,
    status="VERIFIED",
):
    return CanonicalTimeAllocation(
        allocation_id=allocation_id,
        curriculum_ref=curriculum_ref,
        subject_ref=subject_ref,
        grade=grade,
        total_periods=total_periods,
        provenance=TimeAllocationProvenance(
            legal_authority="AUTHORITY",
            regulation_id="REGULATION",
            source_document_id="SOURCE",
        ),
        status=status,
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
        "WR-001D.12C.4 - TIME ALLOCATION "
        "AUTHORITY SOURCE TEST"
    )
    print("=" * 72)

    allocation = make_allocation()

    source = CanonicalCurriculumAuthoritySource(
        facade=FakeFacade(),
        curriculum_refs=(
            "CURR-A",
        ),
        subject_refs=(
            "SUBJECT-A",
        ),
        time_allocations=(
            allocation,
        ),
    )

    results = []

    resolved = source.time_allocation(
        curriculum_ref="CURR-A",
        subject_ref="SUBJECT-A",
        grade=6,
    )

    checks = [
        (
            "TAS1 Verified allocation resolved",
            resolved is allocation,
        ),
        (
            "TAS2 Total periods preserved",
            resolved.total_periods == 123,
        ),
        (
            "TAS3 Unknown grade returns none",
            source.time_allocation(
                curriculum_ref="CURR-A",
                subject_ref="SUBJECT-A",
                grade=7,
            )
            is None,
        ),
        (
            "TAS4 Unsupported curriculum blocked",
            expect_error(
                LookupError,
                lambda: source.time_allocation(
                    curriculum_ref="CURR-X",
                    subject_ref="SUBJECT-A",
                    grade=6,
                ),
            ),
        ),
        (
            "TAS5 Unsupported subject blocked",
            expect_error(
                LookupError,
                lambda: source.time_allocation(
                    curriculum_ref="CURR-A",
                    subject_ref="SUBJECT-X",
                    grade=6,
                ),
            ),
        ),
        (
            "TAS6 Candidate allocation not authoritative",
            CanonicalCurriculumAuthoritySource(
                facade=FakeFacade(),
                curriculum_refs=("CURR-A",),
                subject_refs=("SUBJECT-A",),
                time_allocations=(
                    make_allocation(
                        status="CANDIDATE"
                    ),
                ),
            ).time_allocation(
                curriculum_ref="CURR-A",
                subject_ref="SUBJECT-A",
                grade=6,
            )
            is None,
        ),
        (
            "TAS7 Non-tuple allocation container blocked",
            expect_error(
                TypeError,
                lambda: CanonicalCurriculumAuthoritySource(
                    facade=FakeFacade(),
                    curriculum_refs=("CURR-A",),
                    subject_refs=("SUBJECT-A",),
                    time_allocations=[],
                ),
            ),
        ),
        (
            "TAS8 Invalid allocation item blocked",
            expect_error(
                TypeError,
                lambda: CanonicalCurriculumAuthoritySource(
                    facade=FakeFacade(),
                    curriculum_refs=("CURR-A",),
                    subject_refs=("SUBJECT-A",),
                    time_allocations=("BAD",),
                ),
            ),
        ),
    ]

    duplicate_source = (
        CanonicalCurriculumAuthoritySource(
            facade=FakeFacade(),
            curriculum_refs=("CURR-A",),
            subject_refs=("SUBJECT-A",),
            time_allocations=(
                make_allocation(
                    allocation_id="ALLOC-A"
                ),
                make_allocation(
                    allocation_id="ALLOC-B"
                ),
            ),
        )
    )

    checks.append(
        (
            "TAS9 Multiple verified allocations blocked",
            expect_error(
                ValueError,
                lambda: duplicate_source.time_allocation(
                    curriculum_ref="CURR-A",
                    subject_ref="SUBJECT-A",
                    grade=6,
                ),
            ),
        )
    )

    future_source = (
        CanonicalCurriculumAuthoritySource(
            facade=FakeFacade(),
            curriculum_refs=("CURR-A",),
            subject_refs=("SUBJECT-A",),
            time_allocations=(
                make_allocation(
                    total_periods=321
                ),
            ),
        )
    )

    checks.append(
        (
            "TAS10 Different authority value needs no code change",
            future_source.time_allocation(
                curriculum_ref="CURR-A",
                subject_ref="SUBJECT-A",
                grade=6,
            ).total_periods
            == 321,
        )
    )

    for label, passed in checks:
        results.append(passed)

        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print()

    if all(results):
        print(
            "RESULT: PASS - TIME ALLOCATION "
            "AUTHORITY SOURCE VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - TIME ALLOCATION "
            "AUTHORITY SOURCE VIOLATED"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
