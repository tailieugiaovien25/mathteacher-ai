from typing import Any

from core_v2.processing import Processor, ProcessorRouter
from orchestrator_v2.contracts import DispatchStatus, Task
from orchestrator_v2.dispatch import TaskDispatcher


class EchoProcessor(Processor):
    @property
    def processor_id(self) -> str:
        return "PROC-ECHO"

    @property
    def data_type_id(self) -> str:
        return "ECHO"

    @property
    def capability(self) -> str:
        return "ECHO_DATA"

    def process(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:
        return {
            "data": data,
            "context": context,
        }


class FailingProcessor(Processor):
    @property
    def processor_id(self) -> str:
        return "PROC-FAIL"

    @property
    def data_type_id(self) -> str:
        return "FAIL"

    @property
    def capability(self) -> str:
        return "FAIL_DATA"

    def process(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:
        raise RuntimeError("processor failed")


def make_dispatcher(*processors: Processor) -> TaskDispatcher:
    router = ProcessorRouter()
    for processor in processors:
        router.register(processor)
    return TaskDispatcher(processor_router=router)


def test_dispatch_success():
    dispatcher = make_dispatcher(EchoProcessor())
    task = Task(task_id="TASK-001", capability="ECHO_DATA")

    result = dispatcher.dispatch(
        task=task,
        data_type_id="ECHO",
        data={"value": 1},
    )

    assert result.status is DispatchStatus.SUCCESS
    assert result.processor_id == "PROC-ECHO"
    assert result.result["data"] == {"value": 1}
    assert result.error is None


def test_dispatch_passes_context_to_processor():
    dispatcher = make_dispatcher(EchoProcessor())
    task = Task(task_id="TASK-002", capability="ECHO_DATA")

    result = dispatcher.dispatch(
        task=task,
        data_type_id="ECHO",
        data="hello",
        context={"trace_id": "TRACE-001"},
    )

    assert result.result["context"] == {
        "trace_id": "TRACE-001",
    }


def test_dispatch_no_processor_available():
    dispatcher = make_dispatcher()
    task = Task(task_id="TASK-003", capability="UNKNOWN")

    result = dispatcher.dispatch(
        task=task,
        data_type_id="UNKNOWN",
        data=None,
    )

    assert result.status is DispatchStatus.NO_PROCESSOR_AVAILABLE
    assert result.processor_id is None
    assert result.error


def test_dispatch_processor_failure():
    dispatcher = make_dispatcher(FailingProcessor())
    task = Task(task_id="TASK-004", capability="FAIL_DATA")

    result = dispatcher.dispatch(
        task=task,
        data_type_id="FAIL",
        data={},
    )

    assert result.status is DispatchStatus.FAILED
    assert result.processor_id == "PROC-FAIL"
    assert result.error == "processor failed"


def test_failure_metadata_contains_error_type():
    dispatcher = make_dispatcher(FailingProcessor())
    task = Task(task_id="TASK-005", capability="FAIL_DATA")

    result = dispatcher.dispatch(
        task=task,
        data_type_id="FAIL",
        data={},
    )

    assert result.metadata["error_type"] == "RuntimeError"


def test_dispatch_metadata_preserves_route():
    dispatcher = make_dispatcher(EchoProcessor())
    task = Task(task_id="TASK-006", capability="ECHO_DATA")

    result = dispatcher.dispatch(
        task=task,
        data_type_id="ECHO",
        data={},
    )

    assert result.metadata["data_type_id"] == "ECHO"
    assert result.metadata["capability"] == "ECHO_DATA"


def test_dispatch_preserves_task_id():
    dispatcher = make_dispatcher(EchoProcessor())
    task = Task(task_id="TASK-007", capability="ECHO_DATA")

    result = dispatcher.dispatch(
        task=task,
        data_type_id="ECHO",
        data={},
    )

    assert result.task_id == "TASK-007"


def test_dispatcher_is_domain_neutral():
    dispatcher = make_dispatcher(EchoProcessor())
    task = Task(task_id="TASK-008", capability="ECHO_DATA")

    result = dispatcher.dispatch(
        task=task,
        data_type_id="ECHO",
        data={"domain": "anything"},
    )

    assert result.status is DispatchStatus.SUCCESS
    assert result.result["data"]["domain"] == "anything"
