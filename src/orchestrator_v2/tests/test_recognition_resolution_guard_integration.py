from src.orchestrator_v2.contracts import (
    GuardStatus,
    RecognitionStatus,
)
from src.orchestrator_v2.contracts.recognition_evidence import (
    RecognitionEvidence,
)
from src.orchestrator_v2.guards.orchestrator_guard import (
    OrchestratorGuard,
)
from src.orchestrator_v2.recognition.deterministic_recognition_resolution_policy import (
    DeterministicRecognitionResolutionPolicy,
)
from src.orchestrator_v2.recognition.recognition_resolution_config import (
    RecognitionResolutionConfig,
)


def _evidence(
    data_type_id: str,
    confidence: float,
    authority: float = 1.0,
) -> RecognitionEvidence:
    return RecognitionEvidence(
        provider_id="integration-provider",
        candidate_data_type_id=data_type_id,
        confidence=confidence,
        authority=authority,
    )


def _guard_passed(guard_result) -> bool:
    return (
        guard_result.is_valid is True
        and guard_result.status is GuardStatus.PASS
    )


def main():
    print("=" * 78)
    print(
        "V2-ORCH-005F.7 - RESOLUTION POLICY "
        "<-> ORCHESTRATOR GUARD INTEGRATION TEST"
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

    guard = OrchestratorGuard()

    # G1 - UNRESOLVED result passes Guard
    recognition = policy.resolve(())

    validation = guard.validate_recognition(
        recognition
    )

    passed = (
        recognition.status
        is RecognitionStatus.UNRESOLVED
        and _guard_passed(validation)
    )

    results.append(passed)

    print(
        f"G1 UNRESOLVED result accepted by Guard: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # G2 - RECOGNIZED result passes Guard
    recognition = policy.resolve(
        (
            _evidence(
                "type-a",
                confidence=0.95,
            ),
        )
    )

    validation = guard.validate_recognition(
        recognition
    )

    passed = (
        recognition.status
        is RecognitionStatus.RECOGNIZED
        and recognition.data_type_id
        == "type-a"
        and _guard_passed(validation)
    )

    results.append(passed)

    print(
        f"G2 RECOGNIZED result accepted by Guard: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # G3 - AMBIGUOUS result passes Guard
    recognition = policy.resolve(
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

    validation = guard.validate_recognition(
        recognition
    )

    passed = (
        recognition.status
        is RecognitionStatus.AMBIGUOUS
        and recognition.data_type_id is None
        and len(recognition.candidates) >= 2
        and _guard_passed(validation)
    )

    results.append(passed)

    print(
        f"G3 AMBIGUOUS result accepted by Guard: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # G4 - weak evidence result passes Guard
    recognition = policy.resolve(
        (
            _evidence(
                "type-a",
                confidence=0.70,
            ),
        )
    )

    validation = guard.validate_recognition(
        recognition
    )

    passed = (
        recognition.status
        is RecognitionStatus.UNRESOLVED
        and _guard_passed(validation)
    )

    results.append(passed)

    print(
        f"G4 Weak-result contract accepted by Guard: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # G5 - low-authority result passes Guard
    recognition = policy.resolve(
        (
            _evidence(
                "type-a",
                confidence=0.99,
                authority=0.10,
            ),
        )
    )

    validation = guard.validate_recognition(
        recognition
    )

    passed = (
        recognition.status
        is RecognitionStatus.UNRESOLVED
        and _guard_passed(validation)
    )

    results.append(passed)

    print(
        f"G5 Low-authority result accepted by Guard: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # G6 - all candidate confidences remain valid
    recognition = policy.resolve(
        (
            _evidence(
                "type-a",
                confidence=0.91,
            ),
            _evidence(
                "type-b",
                confidence=0.89,
            ),
        )
    )

    validation = guard.validate_recognition(
        recognition
    )

    candidate_confidences_valid = all(
        0.0 <= candidate.confidence <= 1.0
        for candidate in recognition.candidates
    )

    passed = (
        candidate_confidences_valid
        and _guard_passed(validation)
    )

    results.append(passed)

    print(
        f"G6 Candidate confidence contract preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - RESOLUTION POLICY / "
            "ORCHESTRATOR GUARD INTEGRATION VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - RESOLUTION POLICY / "
            "ORCHESTRATOR GUARD INTEGRATION VIOLATED"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()