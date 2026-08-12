from dataclasses import FrozenInstanceError

from src.multiai_v2.contracts import (
    ProviderHealth,
    ProviderStatus,
)


def _expect_exception(
    exception_type,
    action,
):
    try:
        action()
    except exception_type:
        return True
    except Exception:
        return False

    return False


def main():
    print("=" * 72)
    print(
        "V2-MULTIAI-001C.2 - "
        "PROVIDER HEALTH CONTRACT TEST"
    )
    print("=" * 72)

    results = []

    # H1 - valid health accepted
    health = ProviderHealth(
        status=ProviderStatus.ACTIVE,
        is_available=True,
        latency_ms=120.0,
        failure_rate=0.02,
    )

    passed = (
        health.status is ProviderStatus.ACTIVE
        and health.is_available is True
        and health.latency_ms == 120.0
        and health.failure_rate == 0.02
    )

    results.append(passed)

    print(
        f"H1 Valid health accepted: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # H2 - default values accepted
    health = ProviderHealth(
        status=ProviderStatus.REGISTERED,
        is_available=False,
    )

    passed = (
        health.latency_ms is None
        and health.failure_rate == 0.0
    )

    results.append(passed)

    print(
        f"H2 Default health values accepted: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # H3 - invalid status blocked
    passed = _expect_exception(
        TypeError,
        lambda: ProviderHealth(
            status="ACTIVE",
            is_available=True,
        ),
    )

    results.append(passed)

    print(
        f"H3 Invalid status blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # H4 - invalid availability blocked
    passed = _expect_exception(
        TypeError,
        lambda: ProviderHealth(
            status=ProviderStatus.ACTIVE,
            is_available=1,
        ),
    )

    results.append(passed)

    print(
        f"H4 Invalid availability blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # H5 - negative latency blocked
    passed = _expect_exception(
        ValueError,
        lambda: ProviderHealth(
            status=ProviderStatus.ACTIVE,
            is_available=True,
            latency_ms=-1.0,
        ),
    )

    results.append(passed)

    print(
        f"H5 Negative latency blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # H6 - failure rate below 0 blocked
    passed = _expect_exception(
        ValueError,
        lambda: ProviderHealth(
            status=ProviderStatus.ACTIVE,
            is_available=True,
            failure_rate=-0.01,
        ),
    )

    results.append(passed)

    print(
        f"H6 Negative failure rate blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # H7 - failure rate above 1 blocked
    passed = _expect_exception(
        ValueError,
        lambda: ProviderHealth(
            status=ProviderStatus.ACTIVE,
            is_available=True,
            failure_rate=1.01,
        ),
    )

    results.append(passed)

    print(
        f"H7 Failure rate above 1 blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # H8 - contract is immutable
    health = ProviderHealth(
        status=ProviderStatus.ACTIVE,
        is_available=True,
    )

    passed = _expect_exception(
        FrozenInstanceError,
        lambda: setattr(
            health,
            "failure_rate",
            0.5,
        ),
    )

    results.append(passed)

    print(
        f"H8 Health contract immutable: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # H9 - public import works
    passed = (
        ProviderHealth.__name__
        == "ProviderHealth"
    )

    results.append(passed)

    print(
        f"H9 Public contract import works: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - PROVIDER HEALTH "
            "CONTRACT VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - PROVIDER HEALTH "
            "CONTRACT VIOLATED"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()