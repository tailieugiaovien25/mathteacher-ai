from src.orchestrator_v2.contracts.recognition_evidence import (
    RecognitionEvidence,
)
from src.orchestrator_v2.contracts.recognition_result import (
    RecognitionResult,
    RecognitionStatus,
)
from src.orchestrator_v2.recognition.recognition_resolution_policy import (
    RecognitionResolutionPolicy,
)


class DemoResolutionPolicy(RecognitionResolutionPolicy):
    """
    Minimal concrete implementation used only
    to verify the RecognitionResolutionPolicy contract.
    """

    def __init__(self):
        self.received_evidence = None

    def resolve(
        self,
        evidence: tuple[RecognitionEvidence, ...],
    ) -> RecognitionResult:
        self.received_evidence = evidence

        return RecognitionResult(
            data_type_id="demo-data-type",
            confidence=0.95,
            status=RecognitionStatus.RECOGNIZED,
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
        "V2-ORCH-005F.2 - RECOGNITION "
        "RESOLUTION POLICY CONTRACT TEST"
    )
    print("=" * 76)

    results = []

    # F1 - abstract policy cannot be instantiated
    passed = _expect_exception(
        TypeError,
        lambda: RecognitionResolutionPolicy(),
    )

    results.append(passed)

    print(
        f"F1 Abstract policy protected: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # F2 - concrete implementation can be instantiated
    policy = DemoResolutionPolicy()

    passed = isinstance(
        policy,
        RecognitionResolutionPolicy,
    )

    results.append(passed)

    print(
        f"F2 Concrete policy accepted: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # F3 - evidence tuple reaches policy unchanged
    evidence = (
        RecognitionEvidence(
            provider_id="provider-a",
            candidate_data_type_id="demo-data-type",
            confidence=0.95,
            authority=1.0,
        ),
    )

    result = policy.resolve(evidence)

    passed = (
        policy.received_evidence
        is evidence
    )

    results.append(passed)

    print(
        f"F3 Evidence identity preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # F4 - policy returns RecognitionResult
    passed = isinstance(
        result,
        RecognitionResult,
    )

    results.append(passed)

    print(
        f"F4 RecognitionResult returned: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # F5 - result status contract preserved
    passed = (
        result.status
        is RecognitionStatus.RECOGNIZED
    )

    results.append(passed)

    print(
        f"F5 RecognitionStatus preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # F6 - result data type preserved
    passed = (
        result.data_type_id
        == "demo-data-type"
    )

    results.append(passed)

    print(
        f"F6 Result data_type_id preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # F7 - result confidence preserved
    passed = (
        result.confidence
        == 0.95
    )

    results.append(passed)

    print(
        f"F7 Result confidence preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - RECOGNITION RESOLUTION "
            "POLICY CONTRACT VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - RECOGNITION RESOLUTION "
            "POLICY CONTRACT VIOLATED"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()