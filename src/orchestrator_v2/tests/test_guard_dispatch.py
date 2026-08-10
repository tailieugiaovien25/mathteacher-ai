from src.orchestrator_v2.contracts import (
    DispatchResult,
    DispatchStatus,
)

from src.orchestrator_v2.guards import (
    OrchestratorGuard,
)


def main():

    print("=" * 72)
    print(
        "V2-ORCH-003B-5 - "
        "DISPATCH GUARD TEST"
    )
    print("=" * 72)

    guard = OrchestratorGuard()

    # --------------------------------------------------------
    # G12 - SUCCESS hợp lệ
    # --------------------------------------------------------

    success = DispatchResult(
        task_id="TASK-001",
        processor_id="PROC-001",
        status=DispatchStatus.SUCCESS,
        result={
            "value": "OK",
        },
    )

    before_success = (
        success.task_id,
        success.processor_id,
        success.status,
        success.result,
        success.error,
    )

    result = guard.validate_dispatch(
        success
    )

    assert result.is_valid

    print(
        "G12 valid SUCCESS: PASS"
    )

    # --------------------------------------------------------
    # G12 - SUCCESS thiếu processor
    # --------------------------------------------------------

    missing_processor = DispatchResult(
        task_id="TASK-002",
        processor_id=None,
        status=DispatchStatus.SUCCESS,
        result={
            "value": "INVALID",
        },
    )

    result = guard.validate_dispatch(
        missing_processor
    )

    assert not result.is_valid

    print(
        "G12 SUCCESS without processor blocked: PASS"
    )

    # --------------------------------------------------------
    # G13 - NO_PROCESSOR_AVAILABLE hợp lệ
    # --------------------------------------------------------

    no_processor = DispatchResult(
        task_id="TASK-003",
        processor_id=None,
        status=(
            DispatchStatus.NO_PROCESSOR_AVAILABLE
        ),
        error=(
            "Không có processor phù hợp."
        ),
    )

    result = guard.validate_dispatch(
        no_processor
    )

    assert result.is_valid

    print(
        "G13 valid NO_PROCESSOR_AVAILABLE: PASS"
    )

    # --------------------------------------------------------
    # G13 - NO_PROCESSOR_AVAILABLE
    # nhưng có processor_id
    # --------------------------------------------------------

    invalid_no_processor = DispatchResult(
        task_id="TASK-004",
        processor_id="PROC-999",
        status=(
            DispatchStatus.NO_PROCESSOR_AVAILABLE
        ),
        error=(
            "Trạng thái không nhất quán."
        ),
    )

    result = guard.validate_dispatch(
        invalid_no_processor
    )

    assert not result.is_valid

    print(
        "G13 invalid processor state blocked: PASS"
    )

    # --------------------------------------------------------
    # FAILED hợp lệ
    # --------------------------------------------------------

    failed = DispatchResult(
        task_id="TASK-005",
        processor_id="PROC-001",
        status=DispatchStatus.FAILED,
        error="Processor execution failed.",
    )

    result = guard.validate_dispatch(
        failed
    )

    assert result.is_valid

    print(
        "FAILED with error: PASS"
    )

    # --------------------------------------------------------
    # FAILED thiếu error
    # --------------------------------------------------------

    failed_without_error = DispatchResult(
        task_id="TASK-006",
        processor_id="PROC-001",
        status=DispatchStatus.FAILED,
    )

    result = guard.validate_dispatch(
        failed_without_error
    )

    assert not result.is_valid

    print(
        "FAILED without error blocked: PASS"
    )

    # --------------------------------------------------------
    # G14 - Guard không mutate input
    # --------------------------------------------------------

    after_success = (
        success.task_id,
        success.processor_id,
        success.status,
        success.result,
        success.error,
    )

    assert (
        before_success
        == after_success
    )

    print(
        "G14 Guard does not mutate input: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - DISPATCH GUARD VERIFIED"
    )


if __name__ == "__main__":
    main()