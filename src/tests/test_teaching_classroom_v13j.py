import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_kernel.contracts import AIActionClass
from ai_kernel.teaching_assistant import TeachingAssistantController, TeachingAssistantMode, default_teaching_personas, default_teaching_policy, TeachingAssistantAction
from ai_kernel.teaching_classroom_executor import (
    ClassroomExecutionStatus,
    InMemoryClassroomRuntime,
    TeachingClassroomActionExecutor,
)


def controller():
    persona = default_teaching_personas()[0]
    return TeachingAssistantController(persona=persona, policy=default_teaching_policy(persona.persona_id))


def slide_action():
    return TeachingAssistantAction(
        action_id="a-slide-1",
        tool_id="classroom.slide.open",
        label="Mở slide",
        action_class=AIActionClass.MUTATING,
        arguments={"slide_id": "slide-7"},
        requires_teacher_confirmation=True,
    )


def test_mutating_action_requires_teacher_confirmation():
    ctl = controller()
    exe = TeachingClassroomActionExecutor(controller=ctl, runtime=InMemoryClassroomRuntime())
    result = exe.execute(slide_action())
    assert result.status is ClassroomExecutionStatus.TEACHER_CONFIRMATION_REQUIRED


def test_teacher_confirmation_executes_action():
    ctl = controller()
    runtime = InMemoryClassroomRuntime()
    exe = TeachingClassroomActionExecutor(controller=ctl, runtime=runtime)
    result = exe.execute(slide_action(), teacher_confirmed=True)
    assert result.status is ClassroomExecutionStatus.EXECUTED
    assert runtime.events[-1].tool_id == "classroom.slide.open"
    assert ctl.session.approved_action_ids == ("a-slide-1",)


def test_teacher_override_blocks_ai_execution_even_after_confirmation_request():
    ctl = controller()
    ctl.teacher_take_control()
    exe = TeachingClassroomActionExecutor(controller=ctl, runtime=InMemoryClassroomRuntime())
    result = exe.execute(slide_action(), teacher_confirmed=True)
    assert result.status is ClassroomExecutionStatus.BLOCKED


def test_read_only_status_can_execute_without_teacher_confirmation():
    ctl = controller()
    runtime = InMemoryClassroomRuntime()
    runtime.state["selected_slide_id"] = "slide-2"
    exe = TeachingClassroomActionExecutor(controller=ctl, runtime=runtime)
    action = TeachingAssistantAction(
        action_id="a-status-1",
        tool_id="classroom.status.read",
        label="Đọc trạng thái",
        action_class=AIActionClass.READ_ONLY,
        arguments={},
        requires_teacher_confirmation=False,
    )
    result = exe.execute(action)
    assert result.status is ClassroomExecutionStatus.EXECUTED
    assert result.output["selected_slide_id"] == "slide-2"


def test_plan_action_is_still_subject_to_allowlist():
    ctl = controller()
    runtime = InMemoryClassroomRuntime()
    exe = TeachingClassroomActionExecutor(controller=ctl, runtime=runtime)
    action = TeachingAssistantAction(
        action_id="a-bad-1",
        tool_id="system.production.write",
        label="Write production",
        action_class=AIActionClass.MUTATING,
        arguments={},
        requires_teacher_confirmation=True,
    )
    result = exe.execute(action, teacher_confirmed=True)
    assert result.status is ClassroomExecutionStatus.REJECTED


def test_streamlit_runtime_updates_existing_lesson_slide_contract_and_runtime_state():
    ctl = controller()
    state = {}
    from ai_kernel.teaching_classroom_executor import StreamlitClassroomRuntime
    runtime = StreamlitClassroomRuntime(state)
    exe = TeachingClassroomActionExecutor(controller=ctl, runtime=runtime)
    action = slide_action()
    result = exe.execute(action, teacher_confirmed=True)
    assert result.status is ClassroomExecutionStatus.EXECUTED
    assert state["lesson_slide_selected"] == "slide-7"
    assert state["ta_classroom_runtime_state_v13j"]["selected_slide_id"] == "slide-7"
