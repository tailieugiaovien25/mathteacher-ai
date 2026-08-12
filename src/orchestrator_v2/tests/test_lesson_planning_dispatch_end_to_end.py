from core_v2.processing import ProcessorRouter
from curriculum_v2.canonical_curriculum import get_canonical_curriculum
from educational_planning_v2.builders import PlanItemDraft
from educational_planning_v2 import EducationalPlanningFacade
from lesson_planning_v2.builders import LessonPlanDraft
from lesson_planning_v2.models import LessonPlan, PeriodPlan
from lesson_planning_v2.processors import LessonPlanningProcessor
from orchestrator_v2.contracts import DispatchStatus, Task
from orchestrator_v2.dispatch import TaskDispatcher


def valid_lesson_planning_input() -> dict:
    curriculum = get_canonical_curriculum()
    requirement = curriculum.requirement_by_id("YCCD-MATH-06-0001")
    assert requirement is not None

    educational_plan = EducationalPlanningFacade().build_plan(
        educational_plan_id="EDU-PLAN-MATH-G6-LP-E2E-001",
        academic_year="2026-2027",
        subject="MATHEMATICS",
        grade=6,
        curriculum_ref="CTGDPT-2018-MATH",
        item_drafts=(
            PlanItemDraft(
                title="Bai hoc Lesson Planning E2E",
                periods=1,
                curriculum_node_ids=(
                    requirement.curriculum_node_ref,
                ),
                canonical_requirement_ids=(
                    requirement.canonical_id,
                ),
            ),
        ),
    )

    return {
        "lesson_plan_id": "LESSON-PLAN-MATH-G6-E2E-001",
        "educational_plan": educational_plan,
        "plan_item_id": educational_plan.items[0].plan_item_id,
        "draft": LessonPlanDraft(
            periods=(PeriodPlan(1),),
        ),
    }


def make_dispatcher() -> TaskDispatcher:
    router = ProcessorRouter()
    router.register(LessonPlanningProcessor())
    return TaskDispatcher(processor_router=router)


def make_task(task_id: str) -> Task:
    return Task(
        task_id=task_id,
        capability="BUILD_LESSON_PLAN",
    )


def test_lesson_planning_dispatch_end_to_end_success():
    result = make_dispatcher().dispatch(
        task=make_task("TASK-LESSON-PLAN-E2E-001"),
        data_type_id="LESSON_PLAN",
        data=valid_lesson_planning_input(),
    )

    assert result.status is DispatchStatus.SUCCESS
    assert result.processor_id == "PROC-LESSON-PLANNING-V2"
    assert isinstance(result.result, LessonPlan)


def test_end_to_end_lesson_plan_preserves_canonical_requirement():
    data = valid_lesson_planning_input()
    source_requirement_ids = (
        data["educational_plan"]
        .items[0]
        .curriculum_scope
        .canonical_requirement_ids
    )

    result = make_dispatcher().dispatch(
        task=make_task("TASK-LESSON-PLAN-E2E-002"),
        data_type_id="LESSON_PLAN",
        data=data,
    )

    assert result.status is DispatchStatus.SUCCESS
    assert result.result.canonical_requirement_refs == source_requirement_ids
    assert result.result.canonical_requirement_refs == (
        "YCCD-MATH-06-0001",
    )


def test_end_to_end_lesson_plan_preserves_curriculum_node():
    data = valid_lesson_planning_input()
    source_node_ids = (
        data["educational_plan"]
        .items[0]
        .curriculum_scope
        .curriculum_node_ids
    )

    result = make_dispatcher().dispatch(
        task=make_task("TASK-LESSON-PLAN-E2E-003"),
        data_type_id="LESSON_PLAN",
        data=data,
    )

    assert result.status is DispatchStatus.SUCCESS
    assert result.result.curriculum_node_refs == source_node_ids


def test_end_to_end_lesson_plan_preserves_plan_identity():
    data = valid_lesson_planning_input()
    educational_plan = data["educational_plan"]
    item = educational_plan.items[0]

    result = make_dispatcher().dispatch(
        task=make_task("TASK-LESSON-PLAN-E2E-004"),
        data_type_id="LESSON_PLAN",
        data=data,
    )

    lesson_plan = result.result
    assert lesson_plan.educational_plan_id == educational_plan.educational_plan_id
    assert lesson_plan.plan_item_id == item.plan_item_id
    assert lesson_plan.grade == educational_plan.grade
    assert lesson_plan.total_periods == item.periods


def test_end_to_end_dispatch_preserves_route_metadata():
    task = make_task("TASK-LESSON-PLAN-E2E-005")

    result = make_dispatcher().dispatch(
        task=task,
        data_type_id="LESSON_PLAN",
        data=valid_lesson_planning_input(),
    )

    assert result.status is DispatchStatus.SUCCESS
    assert result.task_id == task.task_id
    assert result.metadata["data_type_id"] == "LESSON_PLAN"
    assert result.metadata["capability"] == "BUILD_LESSON_PLAN"


def test_end_to_end_domain_validation_becomes_failed_dispatch():
    data = valid_lesson_planning_input()
    data["draft"] = LessonPlanDraft(
        plan_mode="SINGLE_PERIOD",
        period_in_lesson=2,
        periods=(PeriodPlan(2),),
    )

    result = make_dispatcher().dispatch(
        task=make_task("TASK-LESSON-PLAN-E2E-006"),
        data_type_id="LESSON_PLAN",
        data=data,
    )

    assert result.status is DispatchStatus.FAILED
    assert result.processor_id == "PROC-LESSON-PLANNING-V2"
    assert result.error is not None
    assert "LESSON_PLAN_PERIOD_INVALID" in result.error


def test_end_to_end_unknown_capability_has_no_processor():
    task = Task(
        task_id="TASK-LESSON-PLAN-E2E-007",
        capability="UNKNOWN_LESSON_PLANNING_CAPABILITY",
    )

    result = make_dispatcher().dispatch(
        task=task,
        data_type_id="LESSON_PLAN",
        data=valid_lesson_planning_input(),
    )

    assert result.status is DispatchStatus.NO_PROCESSOR_AVAILABLE
    assert result.processor_id is None
    assert result.result is None


def test_end_to_end_context_cannot_override_domain_grade():
    result = make_dispatcher().dispatch(
        task=make_task("TASK-LESSON-PLAN-E2E-008"),
        data_type_id="LESSON_PLAN",
        data=valid_lesson_planning_input(),
        context={
            "trace_id": "TRACE-LESSON-E2E-001",
            "grade": 9,
        },
    )

    assert result.status is DispatchStatus.SUCCESS
    assert result.result.grade == 6
