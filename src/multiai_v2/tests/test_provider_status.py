from src.multiai_v2.contracts import ProviderStatus


def main():
    print("=" * 72)
    print("V2-MULTIAI-001A.2 - PROVIDER STATUS CONTRACT TEST")
    print("=" * 72)

    results = []

    expected_values = [
        "REGISTERED",
        "SANDBOX",
        "EVALUATED",
        "APPROVED",
        "ACTIVE",
        "DEGRADED",
        "SUSPENDED",
        "RETIRED",
    ]

    actual_values = [
        status.value
        for status in ProviderStatus
    ]

    # P1 - exact status set
    passed = (
        actual_values
        == expected_values
    )

    results.append(passed)

    print(
        f"P1 Exact status values preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # P2 - enum inherits from str
    passed = all(
        isinstance(
            status.value,
            str,
        )
        for status in ProviderStatus
    )

    results.append(passed)

    print(
        f"P2 Status values are strings: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # P3 - names equal values
    passed = all(
        status.name
        == status.value
        for status in ProviderStatus
    )

    results.append(passed)

    print(
        f"P3 Status names match values: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # P4 - no duplicate values
    passed = (
        len(actual_values)
        == len(set(actual_values))
    )

    results.append(passed)

    print(
        f"P4 No duplicate status values: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # P5 - direct enum lookup works
    passed = (
        ProviderStatus("ACTIVE")
        is ProviderStatus.ACTIVE
    )

    results.append(passed)

    print(
        f"P5 Direct enum lookup works: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # P6 - expected lifecycle endpoints exist
    passed = (
        ProviderStatus.REGISTERED.value
        == "REGISTERED"
        and ProviderStatus.RETIRED.value
        == "RETIRED"
    )

    results.append(passed)

    print(
        f"P6 Lifecycle endpoints preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - PROVIDER STATUS "
            "CONTRACT VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - PROVIDER STATUS "
            "CONTRACT VIOLATED"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()