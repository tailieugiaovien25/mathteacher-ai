from src.orchestrator_v2.contracts.recognition_evidence import (
    RecognitionEvidence,
)
from src.orchestrator_v2.contracts.recognition_result import (
    RecognitionStatus,
)
from src.orchestrator_v2.recognition.recognition_resolution_config import (
    RecognitionResolutionConfig,
)
from src.orchestrator_v2.recognition.deterministic_recognition_resolution_policy import (
    DeterministicRecognitionResolutionPolicy,
)


def _evidence(
    data_type_id: str,
    confidence: float,
    authority: float = 1.0,
    provider_id: str = "test-provider",
) -> RecognitionEvidence:
    return RecognitionEvidence(
        provider_id=provider_id,
        candidate_data_type_id=data_type_id,
        confidence=confidence,
        authority=authority,
    )


def main():
    print("=" * 78)
    print(
        "V2-ORCH-005F.6A - DETERMINISTIC "
        "RECOGNITION RESOLUTION POLICY TEST"
    )
    print("=" * 78)

    results = []

    config = RecognitionResolutionConfig(
        recognized_confidence_threshold=0.80,
        ambiguity_margin=0.05,
        minimum_authority=0.20,
    )

    policy = DeterministicRecognitionResolutionPolicy(
        config
    )

    # ---------------------------------------------------------
    # D1 - No evidence -> UNRESOLVED
    # ---------------------------------------------------------

    result = policy.resolve(())

    passed = (
        result.status is RecognitionStatus.UNRESOLVED
        and result.data_type_id is None
    )

    results.append(passed)

    print(
        f"D1 Empty evidence unresolved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # D2 - One strong candidate -> RECOGNIZED
    # ---------------------------------------------------------

    result = policy.resolve(
        (
            _evidence(
                "type-a",
                confidence=0.90,
                authority=1.0,
            ),
        )
    )

    passed = (
        result.status is RecognitionStatus.RECOGNIZED
        and result.data_type_id == "type-a"
        and result.confidence == 0.90
    )

    results.append(passed)

    print(
        f"D2 Strong candidate recognized: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # D3 - Confidence below threshold -> UNRESOLVED
    # ---------------------------------------------------------

    result = policy.resolve(
        (
            _evidence(
                "type-a",
                confidence=0.79,
                authority=1.0,
            ),
        )
    )

    passed = (
        result.status is RecognitionStatus.UNRESOLVED
        and result.data_type_id is None
    )

    results.append(passed)

    print(
        f"D3 Weak candidate unresolved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # D4 - Authority below minimum -> UNRESOLVED
    # ---------------------------------------------------------

    result = policy.resolve(
        (
            _evidence(
                "type-a",
                confidence=0.95,
                authority=0.19,
            ),
        )
    )

    passed = (
        result.status is RecognitionStatus.UNRESOLVED
        and result.data_type_id is None
    )

    results.append(passed)

    print(
        f"D4 Low-authority evidence rejected: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # D5 - Two strong candidates within ambiguity margin
    #      -> AMBIGUOUS
    # ---------------------------------------------------------

    result = policy.resolve(
        (
            _evidence(
                "type-a",
                confidence=0.90,
            ),
            _evidence(
                "type-b",
                confidence=0.87,
            ),
        )
    )

    candidate_ids = tuple(
        candidate.data_type_id
        for candidate in result.candidates
    )

    passed = (
        result.status is RecognitionStatus.AMBIGUOUS
        and result.data_type_id is None
        and candidate_ids == (
            "type-a",
            "type-b",
        )
    )

    results.append(passed)

    print(
        f"D5 Close candidates ambiguous: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # D6 - Clear winner -> RECOGNIZED
    # ---------------------------------------------------------

    result = policy.resolve(
        (
            _evidence(
                "type-a",
                confidence=0.95,
            ),
            _evidence(
                "type-b",
                confidence=0.80,
            ),
        )
    )

    passed = (
        result.status is RecognitionStatus.RECOGNIZED
        and result.data_type_id == "type-a"
        and result.confidence == 0.95
    )

    results.append(passed)

    print(
        f"D6 Clear winner recognized: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # D7 - Same data type evidence is aggregated
    #
    # Contract for deterministic V1 aggregation:
    # candidate confidence = maximum accepted confidence
    # for that data_type_id.
    # ---------------------------------------------------------

    result = policy.resolve(
        (
            _evidence(
                "type-a",
                confidence=0.82,
                provider_id="provider-1",
            ),
            _evidence(
                "type-a",
                confidence=0.91,
                provider_id="provider-2",
            ),
        )
    )

    passed = (
        result.status is RecognitionStatus.RECOGNIZED
        and result.data_type_id == "type-a"
        and result.confidence == 0.91
    )

    results.append(passed)

    print(
        f"D7 Same candidate aggregated: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # D8 - Input evidence tuple must not be mutated
    # ---------------------------------------------------------

    evidence = (
        _evidence(
            "type-a",
            confidence=0.91,
        ),
    )

    original = evidence

    policy.resolve(evidence)

    passed = (
        evidence is original
        and evidence[0].confidence == 0.91
        and evidence[0].candidate_data_type_id
        == "type-a"
    )

    results.append(passed)

    print(
        f"D8 Evidence input preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - DETERMINISTIC RECOGNITION "
            "RESOLUTION POLICY VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - DETERMINISTIC RECOGNITION "
            "RESOLUTION POLICY VIOLATED"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()