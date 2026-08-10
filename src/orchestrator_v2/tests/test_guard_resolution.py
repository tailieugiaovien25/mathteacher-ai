from src.orchestrator_v2.contracts import (
    ResolutionCandidate,
    ResolutionResult,
    ResolutionStatus,
)

from src.orchestrator_v2.guards import (
    OrchestratorGuard,
)


def main():

    print("=" * 72)
    print(
        "V2-ORCH-003B-3 - "
        "RESOLUTION GUARD TEST"
    )
    print("=" * 72)

    guard = OrchestratorGuard()

    # G4 - RESOLVED hợp lệ
    valid = ResolutionResult(
        data_type_id="COMPETENCY",
        resolved_id="COMP-001",
        confidence=1.0,
        status=ResolutionStatus.RESOLVED,
    )

    result = guard.validate_resolution(
        valid
    )

    assert result.is_valid

    print(
        "G4 valid resolved identity: PASS"
    )

    # G4 - RESOLVED nhưng không có identity
    missing_id = ResolutionResult(
        data_type_id="COMPETENCY",
        resolved_id=None,
        confidence=0.95,
        status=ResolutionStatus.RESOLVED,
    )

    result = guard.validate_resolution(
        missing_id
    )

    assert not result.is_valid

    print(
        "G4 resolved without identity blocked: PASS"
    )

    # G5 - UNRESOLVED hợp lệ
    unresolved = ResolutionResult(
        data_type_id="COMPETENCY",
        resolved_id=None,
        confidence=0.0,
        status=ResolutionStatus.UNRESOLVED,
    )

    result = guard.validate_resolution(
        unresolved
    )

    assert result.is_valid

    print(
        "G5 valid unresolved state: PASS"
    )

    # G5 - UNRESOLVED nhưng lại có identity
    invented_identity = ResolutionResult(
        data_type_id="COMPETENCY",
        resolved_id="COMP-999",
        confidence=0.20,
        status=ResolutionStatus.UNRESOLVED,
    )

    result = guard.validate_resolution(
        invented_identity
    )

    assert not result.is_valid

    print(
        "G5 unresolved with identity blocked: PASS"
    )

    # AMBIGUOUS hợp lệ
    ambiguous = ResolutionResult(
        data_type_id="COMPETENCY",
        resolved_id=None,
        confidence=0.60,
        status=ResolutionStatus.AMBIGUOUS,
        candidates=(
            ResolutionCandidate(
                data_type_id="COMPETENCY",
                resolved_id="COMP-001",
                confidence=0.60,
            ),
            ResolutionCandidate(
                data_type_id="COMPETENCY",
                resolved_id="COMP-002",
                confidence=0.55,
            ),
        ),
    )

    result = guard.validate_resolution(
        ambiguous
    )

    assert result.is_valid

    print(
        "Ambiguous resolution candidates: PASS"
    )

    # AMBIGUOUS không có candidate
    no_candidates = ResolutionResult(
        data_type_id="COMPETENCY",
        resolved_id=None,
        confidence=0.50,
        status=ResolutionStatus.AMBIGUOUS,
    )

    result = guard.validate_resolution(
        no_candidates
    )

    assert not result.is_valid

    print(
        "Ambiguous without candidates blocked: PASS"
    )

    # Confidence sai
    bad_confidence = ResolutionResult(
        data_type_id="COMPETENCY",
        resolved_id="COMP-001",
        confidence=1.5,
        status=ResolutionStatus.RESOLVED,
    )

    result = guard.validate_resolution(
        bad_confidence
    )

    assert not result.is_valid

    print(
        "Invalid resolution confidence blocked: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - RESOLUTION GUARD VERIFIED"
    )


if __name__ == "__main__":
    main()