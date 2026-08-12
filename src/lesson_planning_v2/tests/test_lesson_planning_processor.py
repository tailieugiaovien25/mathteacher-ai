import pytest

from core_v2.processing import Processor, ProcessorRouter
from educational_planning_v2.models import (
    CurriculumScope,
    EducationalPlan,
    EducationalPlanItem,
)
from lesson_planning_v2.builders import LessonPlanDraft
from lesson_planning_v2.models import (
    LessonObjective,
    LessonPlan,
    PeriodPlan,
)
from lesson_planning_v2.processors import LessonPlanningProcessor
from orchestrator_v2.contracts import DispatchStatus, Task
from orchestrator_v2.dispatch import TaskDispatcher


class FakeLessonPlanningFacade:
    def __init__(self):
        self.context_calls = []
        self.plan_calls = []

    def build_context(self, plan, item):
        self.context_calls.append((plan, item))
        return "TRUSTED_CONTEXT"

    def build_plan(self, **kwargs):
        self.plan_calls.append(kwargs)
        return "LESSON_PLAN_RESULT"


def make_educational_plan():
    scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=6,
        curriculum_node_ids=("CURR-NODE-MATH-G6-001",),
        canonical_requirement_ids=("YCCD-MATH-06-0001",),
    )
    item = EducationalPlanItem(
        plan_item_id="EP-001-ITEM-001",
        title="Bài học thử nghiệm",
        curriculum_scope=scope,
        periods=1,
        sequence=1,
    )
    plan = EducationalPlan(
        educational_plan_id="EP-001",
        academic_year="2026-2027",
        subject="MATHEMATICS",
        grade=6,
        items=(item,),
    )
    return plan, item


def make_input(draft=None):
    plan, item = make_educational_plan()
    return {
        "lesson_plan_id": "LP-001",
        "educational_plan": plan,
        "plan_item_id": item.plan_item_id,
        "draft": draft if draft is not None else LessonPlanDraft(
            periods=(PeriodPlan(1),),
        ),
    }


def test_processor_implements_core_contract():
    processor = LessonPlanningProcessor(
        facade=FakeLessonPlanningFacade()
    )

    assert isinstance(processor, Processor)
    assert processor.processor_id == "PROC-LESSON-PLANNING-V2"
    assert processor.data_type_id == "LESSON_PLAN"
    assert processor.capability == "BUILD_LESSON_PLAN"


def test_processor_resolves_plan_item_and_delegates_to_facade():
    facade = FakeLessonPlanningFacade()
    processor = LessonPlanningProcessor(facade=facade)
    data = make_input()

    result = processor.process(data)

    plan = data["educational_plan"]
    item = plan.items[0]
    assert result == "LESSON_PLAN_RESULT"
    assert facade.context_calls == [(plan, item)]
    assert facade.plan_calls[0]["lesson_plan_id"] == "LP-001"
    assert facade.plan_calls[0]["context"] == "TRUSTED_CONTEXT"


def test_processor_accepts_draft_dict_boundary():
    facade = FakeLessonPlanningFacade()
    processor = LessonPlanningProcessor(facade=facade)

    processor.process(
        make_input(
            {
                "plan_mode": "SINGLE_PERIOD",
                "period_in_lesson": 1,
                "periods": (PeriodPlan(1),),
            }
        )
    )

    draft = facade.plan_calls[0]["draft"]
    assert isinstance(draft, LessonPlanDraft)
    assert draft.plan_mode == "SINGLE_PERIOD"
    assert draft.period_in_lesson == 1


def test_processor_rejects_non_dict_input():
    with pytest.raises(TypeError):
        LessonPlanningProcessor(
            facade=FakeLessonPlanningFacade()
        ).process("invalid")


def test_processor_requires_educational_plan_object():
    data = make_input()
    data["educational_plan"] = {}

    with pytest.raises(TypeError, match="EducationalPlan"):
        LessonPlanningProcessor(
            facade=FakeLessonPlanningFacade()
        ).process(data)


def test_processor_rejects_unknown_plan_item():
    data = make_input()
    data["plan_item_id"] = "MISSING"

    with pytest.raises(LookupError, match="not found"):
        LessonPlanningProcessor(
            facade=FakeLessonPlanningFacade()
        ).process(data)


def test_processor_requires_lesson_plan_id():
    data = make_input()
    data["lesson_plan_id"] = ""

    with pytest.raises(ValueError, match="lesson_plan_id"):
        LessonPlanningProcessor(
            facade=FakeLessonPlanningFacade()
        ).process(data)


def test_processor_router_resolves_lesson_planning_capability():
    router = ProcessorRouter()
    processor = LessonPlanningProcessor(
        facade=FakeLessonPlanningFacade()
    )
    router.register(processor)

    resolved = router.resolve(
        data_type_id="LESSON_PLAN",
        capability="BUILD_LESSON_PLAN",
    )

    assert resolved is processor


def test_task_dispatcher_executes_lesson_planning_processor():
    router = ProcessorRouter()
    processor = LessonPlanningProcessor(
        facade=FakeLessonPlanningFacade()
    )
    router.register(processor)
    dispatcher = TaskDispatcher(processor_router=router)
    task = Task(
        task_id="TASK-LP-001",
        capability="BUILD_LESSON_PLAN",
    )

    result = dispatcher.dispatch(
        task=task,
        data_type_id="LESSON_PLAN",
        data=make_input(),
    )

    assert result.status is DispatchStatus.SUCCESS
    assert result.processor_id == "PROC-LESSON-PLANNING-V2"
    assert result.result == "LESSON_PLAN_RESULT"


def test_task_dispatcher_converts_processor_error_to_failed_dispatch():
    router = ProcessorRouter()
    processor = LessonPlanningProcessor(
        facade=FakeLessonPlanningFacade()
    )
    router.register(processor)
    dispatcher = TaskDispatcher(processor_router=router)
    task = Task(
        task_id="TASK-LP-002",
        capability="BUILD_LESSON_PLAN",
    )
    data = make_input()
    data["plan_item_id"] = "MISSING"

    result = dispatcher.dispatch(
        task=task,
        data_type_id="LESSON_PLAN",
        data=data,
    )

    assert result.status is DispatchStatus.FAILED
    assert result.processor_id == "PROC-LESSON-PLANNING-V2"
    assert "not found" in result.error
