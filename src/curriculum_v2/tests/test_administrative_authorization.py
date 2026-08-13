from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from curriculum_v2.governance import (
    AdministrativeVerificationPolicy,
    DataGovernanceRecord,
    DataTrustLevel,
    GovernanceActor,
    GovernanceAuthorizationPolicy,
    GovernancePermission,
    VerificationStatus,
    is_trusted_for_production,
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
        "WR-001D.12C.5C.3 - ADMINISTRATIVE "
        "AUTHORIZATION CONTRACT TEST"
    )
    print("=" * 72)

    results = []

    data_entry_actor = GovernanceActor(
        actor_id="ENTRY-USER",
        permissions=(
            GovernancePermission.ENTER_DATA,
        ),
    )

    verifier = GovernanceActor(
        actor_id="ADMIN-VERIFIER",
        permissions=(
            GovernancePermission.ENTER_DATA,
            GovernancePermission.VERIFY_DATA,
            GovernancePermission.PUBLISH_DATA,
        ),
    )

    publisher = GovernanceActor(
        actor_id="PUBLISHER",
        permissions=(
            GovernancePermission.PUBLISH_DATA,
        ),
    )

    checks = [
        (
            "GAP1 Actor accepted",
            verifier.actor_id
            == "ADMIN-VERIFIER",
        ),
        (
            "GAP2 Enter permission detected",
            data_entry_actor.has_permission(
                GovernancePermission.ENTER_DATA
            ),
        ),
        (
            "GAP3 Missing verify permission detected",
            not data_entry_actor.has_permission(
                GovernancePermission.VERIFY_DATA
            ),
        ),
        (
            "GAP4 Authorized verifier allowed",
            GovernanceAuthorizationPolicy.is_allowed(
                actor=verifier,
                permission=GovernancePermission.VERIFY_DATA,
            ),
        ),
        (
            "GAP5 Unauthorized verifier blocked",
            expect_error(
                PermissionError,
                lambda: GovernanceAuthorizationPolicy.require(
                    actor=data_entry_actor,
                    permission=GovernancePermission.VERIFY_DATA,
                ),
            ),
        ),
        (
            "GAP6 Publisher cannot verify without permission",
            expect_error(
                PermissionError,
                lambda: GovernanceAuthorizationPolicy.require(
                    actor=publisher,
                    permission=GovernancePermission.VERIFY_DATA,
                ),
            ),
        ),
        (
            "GAP7 Non-tuple permissions blocked",
            expect_error(
                TypeError,
                lambda: GovernanceActor(
                    actor_id="BAD",
                    permissions=[
                        GovernancePermission.ENTER_DATA
                    ],
                ),
            ),
        ),
        (
            "GAP8 Invalid permission item blocked",
            expect_error(
                TypeError,
                lambda: GovernanceActor(
                    actor_id="BAD",
                    permissions=("VERIFY_DATA",),
                ),
            ),
        ),
        (
            "GAP9 Empty actor ID blocked",
            expect_error(
                ValueError,
                lambda: GovernanceActor(
                    actor_id=" ",
                    permissions=(),
                ),
            ),
        ),
    ]

    now = datetime.now(
        timezone.utc
    )

    verification = (
        AdministrativeVerificationPolicy
        .create_verification(
            entered_by=data_entry_actor.actor_id,
            verifier=verifier,
            verified_at=now,
            source_reference="SOURCE-A",
        )
    )

    checks.extend([
        (
            "GAP10 Verification created by authorized actor",
            verification.verified_by
            == verifier.actor_id,
        ),
        (
            "GAP11 Entry actor identity preserved",
            verification.entered_by
            == data_entry_actor.actor_id,
        ),
        (
            "GAP12 Unauthorized verification creation blocked",
            expect_error(
                PermissionError,
                lambda: (
                    AdministrativeVerificationPolicy
                    .create_verification(
                        entered_by="ENTRY-USER",
                        verifier=data_entry_actor,
                        verified_at=now,
                    )
                ),
            ),
        ),
    ])

    governance_record = DataGovernanceRecord(
        record_id="GOV-AUTH-001",
        trust_level=DataTrustLevel.ADMIN_VERIFIED,
        verification_status=VerificationStatus.VERIFIED,
        administrative_verification=verification,
    )

    checks.extend([
        (
            "GAP13 Authorized verification supports trusted record",
            is_trusted_for_production(
                governance_record
            ),
        ),
        (
            "GAP14 Actor immutable",
            expect_error(
                FrozenInstanceError,
                lambda: setattr(
                    verifier,
                    "actor_id",
                    "OTHER",
                ),
            ),
        ),
    ])

    duplicate_actor = GovernanceActor(
        actor_id="DUP",
        permissions=(
            GovernancePermission.VERIFY_DATA,
            GovernancePermission.VERIFY_DATA,
        ),
    )

    checks.append(
        (
            "GAP15 Duplicate permissions normalized",
            duplicate_actor.permissions
            == (
                GovernancePermission.VERIFY_DATA,
            ),
        )
    )

    future_permission_actor = GovernanceActor(
        actor_id="SUPERSEDER",
        permissions=(
            GovernancePermission.SUPERSEDE_DATA,
        ),
    )

    checks.append(
        (
            "GAP16 Supersede permission independent",
            future_permission_actor.has_permission(
                GovernancePermission.SUPERSEDE_DATA
            )
            and not future_permission_actor.has_permission(
                GovernancePermission.VERIFY_DATA
            ),
        )
    )

    checks.append(
        (
            "GAP17 Core authorization contains no educational values",
            all(
                token not in repr(
                    GovernanceAuthorizationPolicy.__dict__
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

    if all(results):
        print(
            "RESULT: PASS - ADMINISTRATIVE "
            "AUTHORIZATION CONTRACT VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - ADMINISTRATIVE "
            "AUTHORIZATION CONTRACT VIOLATED"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
