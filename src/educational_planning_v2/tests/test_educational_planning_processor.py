import pytest
from core_v2.processing import Processor, ProcessorRouter
from curriculum_v2.canonical_curriculum import get_canonical_curriculum
from educational_planning_v2.models import EducationalPlan
from educational_planning_v2.processors import EducationalPlanningProcessor
from orchestrator_v2.contracts import DispatchResult, DispatchStatus, Task

def valid_input():
    c = get_canonical_curriculum()
    r = c.requirement_by_id("YCCD-MATH-06-0001")
    assert r is not None
    return {
        "educational_plan_id": "EDU-PLAN-MATH-G6-001",
        "academic_year": "2026-2027",
        "subject": "MATHEMATICS",
        "grade": 6,
        "curriculum_ref": "CTGDPT-2018-MATH",
        "item_drafts": [{
            "title": "Bài học", "periods": 1,
            "curriculum_node_ids": [r.curriculum_node_ref],
            "canonical_requirement_ids": ["YCCD-MATH-06-0001"],
        }],
    }

def test_processor_contract():
    p = EducationalPlanningProcessor()
    assert isinstance(p, Processor)
    assert p.processor_id == "PROC-EDUCATIONAL-PLANNING-V2"
    assert p.data_type_id == "EDUCATIONAL_PLAN"
    assert p.capability == "BUILD_EDUCATIONAL_PLAN"

def test_router_resolves_processor():
    router = ProcessorRouter(); p = EducationalPlanningProcessor(); router.register(p)
    assert router.resolve(data_type_id=p.data_type_id, capability=p.capability) is p

def test_processor_builds_plan():
    result = EducationalPlanningProcessor().process(valid_input())
    assert isinstance(result, EducationalPlan)
    assert result.grade == 6 and len(result.items) == 1

def test_external_draft_is_converted():
    item = EducationalPlanningProcessor().process(valid_input()).items[0]
    assert item.plan_item_id == "EDU-PLAN-MATH-G6-001-ITEM-001"
    assert item.curriculum_scope.canonical_requirement_ids == ("YCCD-MATH-06-0001",)

def test_optional_fields_are_preserved():
    data = valid_input()
    data["item_drafts"][0].update({"planned_time":"Tuần 1","teaching_equipment":["Máy chiếu"],"teaching_location":"Phòng học"})
    item = EducationalPlanningProcessor().process(data).items[0]
    assert item.planned_time == "Tuần 1"
    assert item.teaching_equipment == ("Máy chiếu",)
    assert item.teaching_location == "Phòng học"

def test_non_dict_input_rejected():
    with pytest.raises(TypeError):
        EducationalPlanningProcessor().process("invalid")

def test_domain_validation_not_bypassed():
    data = valid_input(); data["item_drafts"][0]["periods"] = 0
    with pytest.raises(ValueError, match="PLAN_ITEM_PERIODS_INVALID"):
        EducationalPlanningProcessor().process(data)

def test_task_capability_routes():
    task = Task(task_id="TASK-EDU-PLAN-001", capability="BUILD_EDUCATIONAL_PLAN")
    router = ProcessorRouter(); p = EducationalPlanningProcessor(); router.register(p)
    assert router.resolve(data_type_id="EDUCATIONAL_PLAN", capability=task.capability) is p

def test_result_wraps_in_dispatch_result():
    task = Task(task_id="TASK-EDU-PLAN-001", capability="BUILD_EDUCATIONAL_PLAN")
    p = EducationalPlanningProcessor(); plan = p.process(valid_input())
    dispatch = DispatchResult(task_id=task.task_id, processor_id=p.processor_id, status=DispatchStatus.SUCCESS, result=plan)
    assert dispatch.status is DispatchStatus.SUCCESS
    assert dispatch.result is plan

def test_context_does_not_override_domain_input():
    data = valid_input()
    result = EducationalPlanningProcessor().process(data, context={"grade": 9})
    assert result.grade == 6
