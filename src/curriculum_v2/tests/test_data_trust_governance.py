from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from curriculum_v2.governance import (
    AdministrativeVerification,
    DataGovernanceRecord,
    DataTrustLevel,
    VerificationStatus,
    is_trusted_for_production,
)


def expect_error(error_type, action):
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
        "WR-001D.12C.5C.2 - "
        "DATA TRUST & ADMIN GOVERNANCE CONTRACT TEST"
    )
    print("=" * 72)

    now = datetime.now(timezone.utc)

    verification = AdministrativeVerification(
        entered_by="ADMIN-A",
        verified_by="ADMIN-B",
        verified_at=now,
        source_reference="SOURCE-REF-A",
    )

    record = DataGovernanceRecord(
        record_id="GOV-001",
        trust_level=DataTrustLevel.ADMIN_VERIFIED,
        verification_status=VerificationStatus.VERIFIED,
        administrative_verification=verification,
        metadata={
            "scope": "TEST",
        },
    )

    tests = []

    tests.append((
        "DGT1 Admin verified record accepted",
        record.trust_level
        is DataTrustLevel.ADMIN_VERIFIED,
    ))

    tests.append((
        "DGT2 Admin verification preserved",
        record.administrative_verification
        is verification,
    ))

    tests.append((
        "DGT3 Admin verified trusted for production",
        is_trusted_for_production(record),
    ))

    official = DataGovernanceRecord(
        record_id="GOV-002",
        trust_level=DataTrustLevel.OFFICIAL_AUTHORITY,
        verification_status=VerificationStatus.VERIFIED,
    )

    tests.append((
        "DGT4 Verified official authority trusted",
        is_trusted_for_production(official),
    ))

    user_input = DataGovernanceRecord(
        record_id="GOV-003",
        trust_level=DataTrustLevel.USER_INPUT,
        verification_status=VerificationStatus.DRAFT,
    )

    tests.append((
        "DGT5 User input not automatically trusted",
        not is_trusted_for_production(user_input),
    ))

    derived = DataGovernanceRecord(
        record_id="GOV-004",
        trust_level=DataTrustLevel.SYSTEM_DERIVED,
        verification_status=VerificationStatus.DRAFT,
    )

    tests.append((
        "DGT6 System-derived not automatically trusted",
        not is_trusted_for_production(derived),
    ))

    tests.append((
        "DGT7 Admin verification required",
        expect_error(
            ValueError,
            lambda: DataGovernanceRecord(
                record_id="BAD-001",
                trust_level=DataTrustLevel.ADMIN_VERIFIED,
                verification_status=VerificationStatus.VERIFIED,
            ),
        ),
    ))

    tests.append((
        "DGT8 Admin verified status required",
        expect_error(
            ValueError,
            lambda: DataGovernanceRecord(
                record_id="BAD-002",
                trust_level=DataTrustLevel.ADMIN_VERIFIED,
                verification_status=VerificationStatus.DRAFT,
                administrative_verification=verification,
            ),
        ),
    ))

    tests.append((
        "DGT9 System-derived self-promotion blocked",
        expect_error(
            ValueError,
            lambda: DataGovernanceRecord(
                record_id="BAD-003",
                trust_level=DataTrustLevel.SYSTEM_DERIVED,
                verification_status=VerificationStatus.VERIFIED,
            ),
        ),
    ))

    tests.append((
        "DGT10 Admin verification on wrong tier blocked",
        expect_error(
            ValueError,
            lambda: DataGovernanceRecord(
                record_id="BAD-004",
                trust_level=DataTrustLevel.USER_INPUT,
                verification_status=VerificationStatus.DRAFT,
                administrative_verification=verification,
            ),
        ),
    ))

    original_metadata = {
        "scope": "A",
    }

    isolated = DataGovernanceRecord(
        record_id="GOV-005",
        trust_level=DataTrustLevel.USER_INPUT,
        verification_status=VerificationStatus.DRAFT,
        metadata=original_metadata,
    )

    original_metadata["scope"] = "CHANGED"

    tests.append((
        "DGT11 Metadata input isolated",
        isolated.metadata["scope"] == "A",
    ))

    try:
        isolated.metadata["scope"] = "B"
        metadata_immutable = False
    except Exception:
        metadata_immutable = True

    tests.append((
        "DGT12 Metadata immutable",
        metadata_immutable,
    ))

    tests.append((
        "DGT13 Governance record immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                record,
                "record_id",
                "CHANGED",
            ),
        ),
    ))

    tests.append((
        "DGT14 Verification immutable",
        expect_error(
            FrozenInstanceError,
            lambda: setattr(
                verification,
                "verified_by",
                "CHANGED",
            ),
        ),
    ))

    tests.append((
        "DGT15 Empty administrator blocked",
        expect_error(
            ValueError,
            lambda: AdministrativeVerification(
                entered_by=" ",
                verified_by="ADMIN",
                verified_at=now,
            ),
        ),
    ))

    tests.append((
        "DGT16 Invalid verification time blocked",
        expect_error(
            TypeError,
            lambda: AdministrativeVerification(
                entered_by="ADMIN-A",
                verified_by="ADMIN-B",
                verified_at="NOW",
            ),
        ),
    ))

    tests.append((
        "DGT17 Contract contains no educational value",
        all(
            value not in (140, 105, 70, 35)
            for value in DataGovernanceRecord.__dict__.values()
        ),
    ))

    passed = True

    for name, result in tests:
        print(
            f"{name}: "
            f"{'PASS' if result else 'FAIL'}"
        )
        passed = passed and result

    print()

    if passed:
        print(
            "RESULT: PASS - DATA TRUST & "
            "ADMIN GOVERNANCE CONTRACT VERIFIED"
        )
        raise SystemExit(0)

    print(
        "RESULT: FAIL - DATA TRUST & "
        "ADMIN GOVERNANCE CONTRACT VIOLATED"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
