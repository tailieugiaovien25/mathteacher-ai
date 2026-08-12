from core_v2.processing import ProcessorRouter
from curriculum_v2.canonical_curriculum import get_canonical_curriculum
from educational_planning_v2.models import EducationalPlan
from educational_planning_v2.processors import EducationalPlanningProcessor
from orchestrator_v2.contracts import DispatchStatus, Task
from orchestrator_v2.dispatch import TaskDispatcher


def valid_planning_input() -> dict:
    curriculum = get_canonical_curriculum()
    requirement = curriculum.requirement_by_id("YCCD-MATH-06-0001")
    assert requirement is not None

    return {
        "educational_plan_id": "EDU-PLAN-MATH-G6-E2E-001",
        "academic_year": "2026-2027",
        "subject": "MATHEMATICS",
        "grade": 6,
        "curriculum_ref": "CTGDPT-2018-MATH",
        "item_drafts": [
            {
                "title": "Bài học tích hợp E2E",
                "periods": 1,
                "curriculum_node_ids": [
                    requirement.curriculum_node_ref,
                ],
                "canonical_requirement_ids": [
                    requirement.canonical_id,
                ],
            }
        ],
    }


def make_dispatcher() -> TaskDispatcher:
    router = ProcessorRouter()
    router.register(EducationalPlanningProcessor())
    return TaskDispatcher(processor_router=router)


def test_educational_planning_dispatch_end_to_end_success():
    task = Task(
        task_id="TASK-EDU-PLAN-E2E-001",
        capability="BUILD_EDUCATIONAL_PLAN",
    )

    result = make_dispatcher().dispatch(
        task=task,
        data_type_id="EDUCATIONAL_PLAN",
        data=valid_planning_input(),
    )

    assert result.status is DispatchStatus.SUCCESS
    assert result.processor_id == "PROC-EDUCATIONAL-PLANNING-V2"
    assert isinstance(result.result, EducationalPlan)


def test_end_to_end_plan_preserves_canonical_requirement():
    task = Task(
        task_id="TASK-EDU-PLAN-E2E-002",
        capability="BUILD_EDUCATIONAL_PLAN",
    )

    result = make_dispatcher().dispatch(
        task=task,
        data_type_id="EDUCATIONAL_PLAN",
        data=valid_planning_input(),
    )

    item = result.result.items[0]

    assert item.curriculum_scope.canonical_requirement_ids == (
        "YCCD-MATH-06-0001",
    )


def test_end_to_end_dispatch_preserves_route_metadata():
    task = Task(
        task_id="TASK-EDU-PLAN-E2E-003",
        capability="BUILD_EDUCATIONAL_PLAN",
    )

    result = make_dispatcher().dispatch(
        task=task,
        data_type_id="EDUCATIONAL_PLAN",
        data=valid_planning_input(),
    )

    assert result.task_id == task.task_id
    assert result.metadata["data_type_id"] == "EDUCATIONAL_PLAN"
    assert result.metadata["capability"] == "BUILD_EDUCATIONAL_PLAN"


def test_end_to_end_domain_validation_becomes_failed_dispatch():
    data = valid_planning_input()
    data["item_drafts"][0]["periods"] = 0

    task = Task(
        task_id="TASK-EDU-PLAN-E2E-004",
        capability="BUILD_EDUCATIONAL_PLAN",
    )

    result = make_dispatcher().dispatch(
        task=task,
        data_type_id="EDUCATIONAL_PLAN",
        data=data,
    )

    assert result.status is DispatchStatus.FAILED
    assert result.processor_id == "PROC-EDUCATIONAL-PLANNING-V2"
    assert result.error is not None
    assert "PLAN_ITEM_PERIODS_INVALID" in result.error


def test_end_to_end_unknown_capability_has_no_processor():
    task = Task(
        task_id="TASK-EDU-PLAN-E2E-005",
        capability="UNKNOWN_EDUCATIONAL_CAPABILITY",
    )

    result = make_dispatcher().dispatch(
        task=task,
        data_type_id="EDUCATIONAL_PLAN",
        data=valid_planning_input(),
    )

    assert result.status is DispatchStatus.NO_PROCESSOR_AVAILABLE
    assert result.processor_id is None
    assert result.result is None


def test_end_to_end_context_reaches_adapter_without_overriding_domain_data():
    task = Task(
        task_id="TASK-EDU-PLAN-E2E-006",
        capability="BUILD_EDUCATIONAL_PLAN",
    )

    result = make_dispatcher().dispatch(
        task=task,
        data_type_id="EDUCATIONAL_PLAN",
        data=valid_planning_input(),
        context={
            "trace_id": "TRACE-EDU-E2E-001",
            "grade": 9,
        },
    )

    assert result.status is DispatchStatus.SUCCESS
    assert result.result.grade == 6
