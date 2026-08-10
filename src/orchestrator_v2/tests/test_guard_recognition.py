from src.orchestrator_v2.contracts import (
    RecognitionCandidate,
    RecognitionResult,
    RecognitionStatus,
)

from src.orchestrator_v2.guards import (
    OrchestratorGuard,
)


def main():

    print("=" * 72)
    print(
        "V2-ORCH-003B-2 - "
        "RECOGNITION GUARD TEST"
    )
    print("=" * 72)

    guard = OrchestratorGuard()

    # --------------------------------------------------------
    # G1. Valid confidence
    # --------------------------------------------------------

    valid = RecognitionResult(
        data_type_id="COMPETENCY",
        confidence=0.95,
        status=RecognitionStatus.RECOGNIZED,
    )

    result = guard.validate_recognition(
        valid
    )

    assert result.is_valid

    print(
        "G1 valid confidence: PASS"
    )

    # --------------------------------------------------------
    # G1. Invalid confidence
    # --------------------------------------------------------

    invalid_confidence = RecognitionResult(
        data_type_id="COMPETENCY",
        confidence=1.5,
        status=RecognitionStatus.RECOGNIZED,
    )

    result = guard.validate_recognition(
        invalid_confidence
    )

    assert not result.is_valid

    print(
        "G1 invalid confidence blocked: PASS"
    )

    # --------------------------------------------------------
    # G2. RECOGNIZED without type
    # --------------------------------------------------------

    missing_type = RecognitionResult(
        data_type_id=None,
        confidence=0.95,
        status=RecognitionStatus.RECOGNIZED,
    )

    result = guard.validate_recognition(
        missing_type
    )

    assert not result.is_valid

    print(
        "G2 recognized without type blocked: PASS"
    )

    # --------------------------------------------------------
    # G3. AMBIGUOUS requires candidates
    # --------------------------------------------------------

    no_candidates = RecognitionResult(
        data_type_id=None,
        confidence=0.55,
        status=RecognitionStatus.AMBIGUOUS,
    )

    result = guard.validate_recognition(
        no_candidates
    )

    assert not result.is_valid

    print(
        "G3 ambiguous without candidates blocked: PASS"
    )

    # --------------------------------------------------------
    # G3. Valid ambiguous result
    # --------------------------------------------------------

    ambiguous = RecognitionResult(
        data_type_id=None,
        confidence=0.58,
        status=RecognitionStatus.AMBIGUOUS,
        candidates=(
            RecognitionCandidate(
                data_type_id="COMPETENCY",
                confidence=0.58,
            ),
            RecognitionCandidate(
                data_type_id="QUALITY",
                confidence=0.54,
            ),
        ),
    )

    result = guard.validate_recognition(
        ambiguous
    )

    assert result.is_valid

    print(
        "G3 valid ambiguous result: PASS"
    )

    # --------------------------------------------------------
    # Candidate confidence invalid
    # --------------------------------------------------------

    bad_candidate = RecognitionResult(
        data_type_id=None,
        confidence=0.50,
        status=RecognitionStatus.AMBIGUOUS,
        candidates=(
            RecognitionCandidate(
                data_type_id="COMPETENCY",
                confidence=2.0,
            ),
        ),
    )

    result = guard.validate_recognition(
        bad_candidate
    )

    assert not result.is_valid

    print(
        "Candidate invalid confidence blocked: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - RECOGNITION GUARD VERIFIED"
    )


if __name__ == "__main__":
    main()