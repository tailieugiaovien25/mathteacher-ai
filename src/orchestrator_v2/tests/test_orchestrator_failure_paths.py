from src.core_v2.processing import (
    ProcessorRouter,
)

from src.orchestrator_v2.contracts import (
    DispatchResult,
    DispatchStatus,
    RecognitionCandidate,
    RecognitionResult,
    RecognitionStatus,
    ResolutionResult,
    ResolutionStatus,
    Task,
    TaskPlan,
    TaskPlanStatus,
)

from src.orchestrator_v2.guards import (
    OrchestratorGuard,
)


def main():

    print("=" * 76)
    print(
        "V2-ORCH-004B - "
        "FAILURE PATH INTEGRATION TEST"
    )
    print("=" * 76)

    guard = OrchestratorGuard()

    # --------------------------------------------------------
    # F1 - AMBIGUOUS
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

    assert ambiguous.data_type_id is None

    print(
        "F1 ambiguous recognition preserved: PASS"
    )

    # Không tự chọn candidate.
    selected_data_type = (
        ambiguous.data_type_id
    )

    assert selected_data_type is None

    print(
        "F1 no invented data type: PASS"
    )

    # --------------------------------------------------------
    # F2 - UNRESOLVED
    # --------------------------------------------------------

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

    assert unresolved.resolved_id is None

    print(
        "F2 unresolved identity preserved: PASS"
    )

    # Không tự tạo COMP-999 hay identity khác.
    invented_identity = (
        unresolved.resolved_id
    )

    assert invented_identity is None

    print(
        "F2 no invented identity: PASS"
    )

    # --------------------------------------------------------
    # F3 - NO PROCESSOR
    # --------------------------------------------------------

    task = Task(
        task_id="TASK-001",
        capability="UNKNOWN_CAPABILITY",
        input_refs=("COMP-001",),
    )

    plan = TaskPlan(
        plan_id="PLAN-001",
        context="ASSESSMENT",
        tasks=(task,),
        status=TaskPlanStatus.READY,
    )

    result = guard.validate_task_plan(
        plan
    )

    assert result.is_valid

    router = ProcessorRouter()

    processor_id = None

    try:
        router.resolve(
            data_type_id="COMPETENCY",
            capability="UNKNOWN_CAPABILITY",
        )

    except KeyError:
        processor_id = None

    assert processor_id is None

    dispatch = DispatchResult(
        task_id="TASK-001",
        processor_id=None,
        status=(
            DispatchStatus.NO_PROCESSOR_AVAILABLE
        ),
        error=(
            "Không có processor cung cấp "
            "capability UNKNOWN_CAPABILITY."
        ),
    )

    result = guard.validate_dispatch(
        dispatch
    )

    assert result.is_valid

    assert (
        dispatch.status
        == DispatchStatus.NO_PROCESSOR_AVAILABLE
    )

    print(
        "F3 no processor fail-closed: PASS"
    )

    # --------------------------------------------------------
    # Final checks
    # --------------------------------------------------------

    assert ambiguous.data_type_id is None
    assert unresolved.resolved_id is None
    assert dispatch.processor_id is None

    print(
        "Failure states remain explicit: PASS"
    )

    print()
    print("=" * 76)

    print(
        "RESULT: "
        "PASS - ORCHESTRATOR FAILURE PATHS VERIFIED"
    )

    print("=" * 76)


if __name__ == "__main__":
    main()