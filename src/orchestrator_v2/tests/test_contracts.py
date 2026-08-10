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


def main():

    print("=" * 72)
    print(
        "V2-ORCH-002B - "
        "ORCHESTRATOR CONTRACT TEST"
    )
    print("=" * 72)

    # --------------------------------------------------------
    # C1. RECOGNIZED
    # --------------------------------------------------------

    recognized = RecognitionResult(
        data_type_id="COMPETENCY",
        confidence=0.96,
        status=RecognitionStatus.RECOGNIZED,
    )

    assert recognized.data_type_id == "COMPETENCY"
    assert recognized.confidence == 0.96
    assert (
        recognized.status
        == RecognitionStatus.RECOGNIZED
    )

    print(
        "C1 recognized contract: PASS"
    )

    # --------------------------------------------------------
    # C2. AMBIGUOUS + candidates
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

    assert ambiguous.data_type_id is None
    assert len(ambiguous.candidates) == 2

    print(
        "C2 ambiguous candidates: PASS"
    )

    # --------------------------------------------------------
    # C3. UNRESOLVED must not invent identity
    # --------------------------------------------------------

    unresolved = ResolutionResult(
        data_type_id="COMPETENCY",
        resolved_id=None,
        confidence=0.0,
        status=ResolutionStatus.UNRESOLVED,
    )

    assert unresolved.resolved_id is None
    assert (
        unresolved.status
        == ResolutionStatus.UNRESOLVED
    )

    print(
        "C3 unresolved fail-closed: PASS"
    )

    # --------------------------------------------------------
    # C4. Task dependency
    # --------------------------------------------------------

    task_1 = Task(
        task_id="TASK-001",
        capability="RESOLVE_MAPPING",
        input_refs=("COMP-001",),
    )

    task_2 = Task(
        task_id="TASK-002",
        capability="ASSESSMENT_GENERATE",
        input_refs=("COMP-001",),
        depends_on=("TASK-001",),
    )

    plan = TaskPlan(
        plan_id="PLAN-001",
        context="ASSESSMENT",
        tasks=(
            task_1,
            task_2,
        ),
        status=TaskPlanStatus.READY,
    )

    assert len(plan.tasks) == 2

    assert (
        plan.tasks[1].depends_on
        == ("TASK-001",)
    )

    print(
        "C4 task dependency: PASS"
    )

    # --------------------------------------------------------
    # C5. P10:
    # Task knows capability, not processor.
    # --------------------------------------------------------

    task_fields = set(
        task_1.__dataclass_fields__
    )

    assert "capability" in task_fields
    assert "processor_id" not in task_fields

    print(
        "C5 P10 capability-based task: PASS"
    )

    # --------------------------------------------------------
    # C6. No processor = explicit failure
    # --------------------------------------------------------

    no_processor = DispatchResult(
        task_id="TASK-002",
        processor_id=None,
        status=(
            DispatchStatus.NO_PROCESSOR_AVAILABLE
        ),
        error=(
            "No processor provides "
            "ASSESSMENT_GENERATE."
        ),
    )

    assert no_processor.processor_id is None

    assert (
        no_processor.status
        == DispatchStatus.NO_PROCESSOR_AVAILABLE
    )

    assert no_processor.result is None

    print(
        "C6 no processor fail-closed: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - ORCHESTRATOR CONTRACTS VERIFIED"
    )


if __name__ == "__main__":
    main()