from __future__ import annotations

from typing import Any

from core_v2.processing import ProcessorRouter
from orchestrator_v2.contracts import (
    DispatchResult,
    DispatchStatus,
    Task,
)
from orchestrator_v2.guards import OrchestratorGuard


class TaskDispatcher:
    """Generic bridge from an orchestrator Task to a Core V2 Processor."""

    def __init__(
        self,
        *,
        processor_router: ProcessorRouter,
        guard: OrchestratorGuard | None = None,
    ) -> None:
        self._processor_router = processor_router
        self._guard = guard or OrchestratorGuard()

    def dispatch(
        self,
        *,
        task: Task,
        data_type_id: str,
        data: Any,
        context: dict[str, Any] | None = None,
    ) -> DispatchResult:
        try:
            processor = self._processor_router.resolve(
                data_type_id=data_type_id,
                capability=task.capability,
            )
        except KeyError as exc:
            result = DispatchResult(
                task_id=task.task_id,
                processor_id=None,
                status=DispatchStatus.NO_PROCESSOR_AVAILABLE,
                error=str(exc),
                metadata={
                    "data_type_id": data_type_id,
                    "capability": task.capability,
                },
            )
            return self._validated(result)

        try:
            output = processor.process(
                data,
                context=context,
            )
        except Exception as exc:
            result = DispatchResult(
                task_id=task.task_id,
                processor_id=processor.processor_id,
                status=DispatchStatus.FAILED,
                error=str(exc),
                metadata={
                    "data_type_id": data_type_id,
                    "capability": task.capability,
                    "error_type": type(exc).__name__,
                },
            )
            return self._validated(result)

        result = DispatchResult(
            task_id=task.task_id,
            processor_id=processor.processor_id,
            status=DispatchStatus.SUCCESS,
            result=output,
            metadata={
                "data_type_id": data_type_id,
                "capability": task.capability,
            },
        )
        return self._validated(result)

    def _validated(
        self,
        result: DispatchResult,
    ) -> DispatchResult:
        guard_result = self._guard.validate_dispatch(result)

        if not guard_result.is_valid:
            codes = ", ".join(
                issue.code
                for issue in guard_result.issues
            )
            raise ValueError(
                f"Invalid DispatchResult: {codes}"
            )

        return result
