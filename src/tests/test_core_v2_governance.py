from src.core_v2.governance import (
    GovernancePolicy,
    LifecycleStatus,
    RetentionPolicy,
    UpdatePolicy,
)


def main():

    print("=" * 72)
    print(
        "V2-CORE-009 - "
        "GOVERNANCE FOUNDATION TEST"
    )
    print("=" * 72)

    policy = GovernancePolicy(
        update_policy=UpdatePolicy.CONTROLLED,
        retention_policy=RetentionPolicy.ACTIVE_FIRST,
        publish_required=True,
        allow_overwrite_before_publish=True,
        allow_hard_delete=True,
    )

    assert policy.should_use_in_engine(
        LifecycleStatus.ACTIVE
    )

    assert not policy.should_use_in_engine(
        LifecycleStatus.ARCHIVED
    )

    print(
        "Active data first: PASS"
    )

    assert policy.can_hard_delete(
        status=LifecycleStatus.DRAFT,
        is_referenced=False,
    )

    print(
        "Unreferenced draft delete: PASS"
    )

    assert not policy.can_hard_delete(
        status=LifecycleStatus.ACTIVE,
        is_referenced=False,
    )

    print(
        "Active hard delete blocked: PASS"
    )

    assert not policy.can_hard_delete(
        status=LifecycleStatus.ARCHIVED,
        is_referenced=True,
    )

    print(
        "Referenced history protected: PASS"
    )

    strict_policy = GovernancePolicy(
        update_policy=UpdatePolicy.VERSIONED,
        retention_policy=RetentionPolicy.KEEP_HISTORY,
        publish_required=True,
        allow_overwrite_before_publish=False,
        allow_hard_delete=False,
    )

    assert strict_policy.should_use_in_engine(
        LifecycleStatus.ACTIVE
    )

    assert strict_policy.should_use_in_engine(
        LifecycleStatus.ARCHIVED
    )

    assert not strict_policy.can_hard_delete(
        status=LifecycleStatus.DRAFT,
        is_referenced=False,
    )

    print(
        "Versioned history policy: PASS"
    )

    print()

    print(
        "RESULT: "
        "PASS - GOVERNANCE FOUNDATION VERIFIED"
    )


if __name__ == "__main__":
    main()