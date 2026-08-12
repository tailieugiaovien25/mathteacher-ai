from dataclasses import FrozenInstanceError

from src.multiai_v2.contracts import (
    ProviderCapability,
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
        "V2-MULTIAI-001B.2 - "
        "PROVIDER CAPABILITY CONTRACT TEST"
    )
    print("=" * 72)

    results = []

    # C1 - valid capability accepted
    capability = ProviderCapability(
        capability_id="generate_text",
        version="1.0",
    )

    passed = (
        capability.capability_id
        == "generate_text"
        and capability.version
        == "1.0"
    )

    results.append(passed)

    print(
        f"C1 Valid capability accepted: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # C2 - capability_id normalized
    capability = ProviderCapability(
        capability_id="  generate_text  ",
        version="1.0",
    )

    passed = (
        capability.capability_id
        == "generate_text"
    )

    results.append(passed)

    print(
        f"C2 Capability ID normalized: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # C3 - version normalized
    capability = ProviderCapability(
        capability_id="generate_text",
        version="  1.0  ",
    )

    passed = (
        capability.version
        == "1.0"
    )

    results.append(passed)

    print(
        f"C3 Version normalized: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # C4 - empty capability_id blocked
    passed = _expect_exception(
        ValueError,
        lambda: ProviderCapability(
            capability_id="   ",
            version="1.0",
        ),
    )

    results.append(passed)

    print(
        f"C4 Empty capability ID blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # C5 - empty version blocked
    passed = _expect_exception(
        ValueError,
        lambda: ProviderCapability(
            capability_id="generate_text",
            version="   ",
        ),
    )

    results.append(passed)

    print(
        f"C5 Empty version blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # C6 - contract is immutable
    capability = ProviderCapability(
        capability_id="generate_text",
        version="1.0",
    )

    passed = _expect_exception(
        FrozenInstanceError,
        lambda: setattr(
            capability,
            "version",
            "2.0",
        ),
    )

    results.append(passed)

    print(
        f"C6 Capability immutable: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # C7 - public contract import works
    passed = (
        ProviderCapability.__name__
        == "ProviderCapability"
    )

    results.append(passed)

    print(
        f"C7 Public contract import works: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - PROVIDER CAPABILITY "
            "CONTRACT VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - PROVIDER CAPABILITY "
            "CONTRACT VIOLATED"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()