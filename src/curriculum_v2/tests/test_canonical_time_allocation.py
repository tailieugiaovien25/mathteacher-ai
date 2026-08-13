from dataclasses import FrozenInstanceError

from curriculum_v2.models.canonical_time_allocation import (
    CanonicalTimeAllocation,
    TimeAllocationProvenance,
)


def expect_error(error_type, action):
    try:
        action()
    except error_type:
        return True
    except Exception:
        return False
    return False


def make_provenance():
    return TimeAllocationProvenance(
        legal_authority="AUTHORITY",
        regulation_id="REGULATION",
        source_document_id="SOURCE",
        source_location="SECTION",
        source_version="VERSION-A",
    )


def make_allocation(**overrides):
    data = {
        "allocation_id": "ALLOC-A",
        "curriculum_ref": "CURRICULUM-A",
        "subject_ref": "SUBJECT-A",
        "grade": 6,
        "total_periods": 123,
        "provenance": make_provenance(),
        "status": "VERIFIED",
        "schema_version": 1,
    }
    data.update(overrides)
    return CanonicalTimeAllocation(**data)


def main():
    print("=" * 72)
    print(
        "WR-001D.12C.3 - CANONICAL TIME ALLOCATION CONTRACT TEST"
    )
    print("=" * 72)

    allocation = make_allocation()

    tests = []

    tests.append((
        "CTA1 Valid allocation accepted",
        allocation.total_periods == 123,
    ))

    tests.append((
        "CTA2 Identity preserved",
        allocation.allocation_id == "ALLOC-A",
    ))

    tests.append((
        "CTA3 Curriculum reference preserved",
        allocation.curriculum_ref == "CURRICULUM-A",
    ))

    tests.append((
        "CTA4 Subject reference preserved",
        allocation.subject_ref == "SUBJECT-A",
    ))

    tests.append((
        "CTA5 Grade preserved",
        allocation.grade == 6,
    ))

    tests.append((
        "CTA6 Status normalized",
        make_allocation(
            status=" verified "
        ).status == "VERIFIED",
    ))

    tests.append((
        "CTA7 Provenance preserved",
        allocation.provenance.source_document_id == "SOURCE",
    ))

    tests.append((
        "CTA8 Empty allocation ID blocked",
        expect_error(
            ValueError,
            lambda: make_allocation(
                allocation_id=" "
            ),
        ),
    ))

    tests.append((
        "CTA9 Invalid grade blocked",
        expect_error(
            ValueError,
            lambda: make_allocation(
                grade=0
            ),
        ),
    ))

    tests.append((
        "CTA10 Boolean grade blocked",
        expect_error(
            TypeError,
            lambda: make_allocation(
                grade=True
            ),
        ),
    ))

    tests.append((
        "CTA11 Non-positive periods blocked",
        expect_error(
            ValueError,
            lambda: make_allocation(
                total_periods=0
            ),
        ),
    ))

    tests.append((
        "CTA12 Boolean periods blocked",
        expect_error(
            TypeError,
            lambda: make_allocation(
                total_periods=True
            ),
        ),
    ))

    tests.append((
        "CTA13 Invalid provenance blocked",
        expect_error(
            TypeError,
            lambda: make_allocation(
                provenance="SOURCE"
            ),
        ),
    ))

    tests.append((
        "CTA14 Invalid status blocked",
        expect_error(
            ValueError,
            lambda: make_allocation(
                status="UNKNOWN"
            ),
        ),
    ))

    tests.append((
        "CTA15 Invalid schema version blocked",
        expect_error(
            ValueError,
            lambda: make_allocation(
                schema_version=0
            ),
        ),
    ))

    tests.append((
        "CTA16 Allocation immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                allocation,
                "total_periods",
                999,
            ),
        ),
    ))

    tests.append((
        "CTA17 Provenance immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                allocation.provenance,
                "regulation_id",
                "OTHER",
            ),
        ),
    ))

    tests.append((
        "CTA18 Contract contains no fixed educational value",
        (
            140 not in CanonicalTimeAllocation.__dict__.values()
            and 105 not in CanonicalTimeAllocation.__dict__.values()
            and 70 not in CanonicalTimeAllocation.__dict__.values()
            and 35 not in CanonicalTimeAllocation.__dict__.values()
        ),
    ))

    failed = False

    for name, passed in tests:
        print(
            f"{name}: "
            f"{'PASS' if passed else 'FAIL'}"
        )
        if not passed:
            failed = True

    print()

    if failed:
        print(
            "RESULT: FAIL - "
            "CANONICAL TIME ALLOCATION CONTRACT VIOLATED"
        )
        raise SystemExit(1)

    print(
        "RESULT: PASS - "
        "CANONICAL TIME ALLOCATION CONTRACT VERIFIED"
    )


if __name__ == "__main__":
    main()
