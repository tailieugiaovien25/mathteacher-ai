from dataclasses import FrozenInstanceError

from src.orchestrator_v2.recognition.recognition_resolution_config import (
    RecognitionResolutionConfig,
)


def _expect_exception(exception_type, action):
    try:
        action()
    except exception_type:
        return True
    except Exception:
        return False

    return False


def main():
    print("=" * 76)
    print(
        "V2-ORCH-005F.5B - RECOGNITION "
        "RESOLUTION CONFIG CONTRACT TEST"
    )
    print("=" * 76)

    results = []

    # C1 - default configuration is valid
    config = RecognitionResolutionConfig()

    passed = (
        config.recognized_confidence_threshold == 0.80
        and config.ambiguity_margin == 0.05
        and config.minimum_authority == 0.00
    )

    results.append(passed)

    print(
        f"C1 Default configuration valid: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # C2 - custom valid configuration accepted
    config = RecognitionResolutionConfig(
        recognized_confidence_threshold=0.90,
        ambiguity_margin=0.10,
        minimum_authority=0.25,
    )

    passed = (
        config.recognized_confidence_threshold == 0.90
        and config.ambiguity_margin == 0.10
        and config.minimum_authority == 0.25
    )

    results.append(passed)

    print(
        f"C2 Custom configuration accepted: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # C3 - recognized threshold below 0 blocked
    passed = _expect_exception(
        ValueError,
        lambda: RecognitionResolutionConfig(
            recognized_confidence_threshold=-0.01
        ),
    )

    results.append(passed)

    print(
        f"C3 Negative recognition threshold blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # C4 - recognized threshold above 1 blocked
    passed = _expect_exception(
        ValueError,
        lambda: RecognitionResolutionConfig(
            recognized_confidence_threshold=1.01
        ),
    )

    results.append(passed)

    print(
        f"C4 Recognition threshold above 1 blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # C5 - invalid ambiguity margin blocked
    passed = _expect_exception(
        ValueError,
        lambda: RecognitionResolutionConfig(
            ambiguity_margin=1.01
        ),
    )

    results.append(passed)

    print(
        f"C5 Invalid ambiguity margin blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # C6 - invalid minimum authority blocked
    passed = _expect_exception(
        ValueError,
        lambda: RecognitionResolutionConfig(
            minimum_authority=-0.01
        ),
    )

    results.append(passed)

    print(
        f"C6 Invalid minimum authority blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # C7 - configuration is immutable
    config = RecognitionResolutionConfig()

    passed = _expect_exception(
        FrozenInstanceError,
        lambda: setattr(
            config,
            "ambiguity_margin",
            0.20,
        ),
    )

    results.append(passed)

    print(
        f"C7 Configuration immutable: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - RECOGNITION RESOLUTION "
            "CONFIG CONTRACT VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - RECOGNITION RESOLUTION "
            "CONFIG CONTRACT VIOLATED"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()