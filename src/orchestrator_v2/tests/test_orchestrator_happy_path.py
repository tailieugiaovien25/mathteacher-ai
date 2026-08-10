from typing import Any

from src.core_v2.processing import (
    Processor,
    ProcessorRouter,
)

from src.orchestrator_v2.contracts import (
    DispatchResult,
    DispatchStatus,
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


class FakeCompetencyProcessor(
    Processor
):

    @property
    def processor_id(self) -> str:
        return "PROC-COMP-001"

    @property
    def data_type_id(self) -> str:
        return "COMPETENCY"

    @property
    def capability(self) -> str:
        return "USE_COMPETENCY"

    def process(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:

        return {
            "processed": True,
            "data": data,
            "context": context or {},
        }


def main():

    print("=" * 76)
    print(
        "V2-ORCH-004A - "
        "HAPPY PATH INTEGRATION TEST"
    )
    print("=" * 76)

    guard = OrchestratorGuard()

    # --------------------------------------------------------
    # 1. Recognition
    # --------------------------------------------------------

    recognition = RecognitionResult(
        data_type_id="COMPETENCY",
        confidence=0.98,
        status=RecognitionStatus.RECOGNIZED,
    )

    recognition_guard = (
        guard.validate_recognition(
            recognition
        )
    )

    assert recognition_guard.is_valid

    print(
        "1. Recognition Guard: PASS"
    )

    # --------------------------------------------------------
    # 2. Resolution
    # --------------------------------------------------------

    resolution = ResolutionResult(
        data_type_id="COMPETENCY",
        resolved_id="COMP-001",
        confidence=1.0,
        status=ResolutionStatus.RESOLVED,
    )

    resolution_guard = (
        guard.validate_resolution(
            resolution
        )
    )

    assert resolution_guard.is_valid

    print(
        "2. Resolution Guard: PASS"
    )

    # --------------------------------------------------------
    # 3. Task Plan
    # --------------------------------------------------------

    task = Task(
        task_id="TASK-001",
        capability="USE_COMPETENCY",
        input_refs=(
            "COMP-001",
        ),
    )

    plan = TaskPlan(
        plan_id="PLAN-001",
        context="LESSON_PLAN",
        tasks=(
            task,
        ),
        status=TaskPlanStatus.READY,
    )

    task_plan_guard = (
        guard.validate_task_plan(
            plan
        )
    )

    assert task_plan_guard.is_valid

    print(
        "3. TaskPlan Guard: PASS"
    )

    # --------------------------------------------------------
    # 4. Processor Router
    # --------------------------------------------------------

    router = ProcessorRouter()

    processor = FakeCompetencyProcessor()

    router.register(
        processor
    )

    resolved_processor = (
        router.resolve(
            data_type_id="COMPETENCY",
            capability="USE_COMPETENCY",
        )
    )

    assert (
        resolved_processor
        is processor
    )

    print(
        "4. Processor Routing: PASS"
    )

    # --------------------------------------------------------
    # 5. Processor execution
    # --------------------------------------------------------

    processor_result = (
        resolved_processor.process(
            {
                "competency_id": "COMP-001",
                "name": (
                    "Tư duy và lập luận toán học"
                ),
            },
            context={
                "product": "LESSON_PLAN",
            },
        )
    )

    assert (
        processor_result["processed"]
        is True
    )

    print(
        "5. Processor Execution: PASS"
    )

    # --------------------------------------------------------
    # 6. Dispatch Result
    # --------------------------------------------------------

    dispatch = DispatchResult(
        task_id="TASK-001",
        processor_id=(
            resolved_processor.processor_id
        ),
        status=DispatchStatus.SUCCESS,
        result=processor_result,
    )

    dispatch_guard = (
        guard.validate_dispatch(
            dispatch
        )
    )

    assert dispatch_guard.is_valid

    print(
        "6. Dispatch Guard: PASS"
    )

    # --------------------------------------------------------
    # 7. P10 check
    # --------------------------------------------------------

    task_fields = set(
        task.__dataclass_fields__
    )

    assert "capability" in task_fields

    assert (
        "processor_id"
        not in task_fields
    )

    print(
        "7. P10 Capability Dispatch: PASS"
    )

    # --------------------------------------------------------
    # 8. End result
    # --------------------------------------------------------

    assert (
        dispatch.result[
            "data"
        ][
            "competency_id"
        ]
        == "COMP-001"
    )

    assert (
        dispatch.result[
            "context"
        ][
            "product"
        ]
        == "LESSON_PLAN"
    )

    print(
        "8. Final Result: PASS"
    )

    print()
    print("=" * 76)

    print(
        "RESULT: "
        "PASS - ORCHESTRATOR HAPPY PATH VERIFIED"
    )

    print("=" * 76)


if __name__ == "__main__":
    main()