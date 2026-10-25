import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_kernel.contracts import AIActionClass
from ai_kernel.teaching_assistant import (
    TeachingAssistantController,
    TeachingAssistantAction,
    default_teaching_personas,
    default_teaching_policy,
)
from ai_kernel.teaching_classroom import ClassroomPhase, LessonActivityContext, TeachingClassroomOrchestrator
from ai_kernel.teaching_classroom_executor import (
    ClassroomExecutionStatus,
    StreamlitClassroomRuntime,
    TeachingClassroomActionExecutor,
)
from ai_kernel.teaching_classroom_surface import build_runtime_overlay_html


def _controller():
    persona = default_teaching_personas()[0]
    return TeachingAssistantController(persona=persona, policy=default_teaching_policy(persona.persona_id))


def test_plan_can_include_real_presentation_controls():
    context = LessonActivityContext(
        lesson_id="lesson-1", activity_id="opening", activity_title="Khởi động",
        phase=ClassroomPhase.OPENING, objective="Ôn tập", duration_seconds=30,
        selected_slide_id="slide-2", stage_content_id="tool-1", question="Em nhận thấy gì?",
        allowed_tools=(
            "classroom.slide.open", "classroom.stage.show", "classroom.timer.start",
            "classroom.quiz.display", "classroom.whiteboard.show",
        ),
    )
    plan = TeachingClassroomOrchestrator().build_plan(
        context=context,
        mode=__import__("ai_kernel.teaching_assistant", fromlist=["TeachingAssistantMode"]).TeachingAssistantMode.MC,
        include_slide=True, include_timer=True, include_quiz=True, include_stage=True, include_whiteboard=True,
    )
    assert {a.tool_id for a in plan.actions} == {
        "classroom.slide.open", "classroom.timer.start", "classroom.quiz.display",
        "classroom.stage.show", "classroom.whiteboard.show",
    }


def test_runtime_rejects_stage_not_prepared():
    state = {"lesson_integrated_stages": {"tool-2": b"<html></html>"}}
    runtime = StreamlitClassroomRuntime(state)
    ctl = _controller()
    exe = TeachingClassroomActionExecutor(controller=ctl, runtime=runtime)
    action = TeachingAssistantAction(
        action_id="stage-1", tool_id="classroom.stage.show", label="Mở sân khấu",
        action_class=AIActionClass.MUTATING,
        arguments={"content_id": "tool-1", "title": "Sân khấu"},
        requires_teacher_confirmation=True,
    )
    result = exe.execute(action, teacher_confirmed=True)
    assert result.status is ClassroomExecutionStatus.FAILED
    assert "chưa được chuẩn bị" in result.message


def test_runtime_updates_quiz_timer_whiteboard_state():
    state = {}
    runtime = StreamlitClassroomRuntime(state)
    ctl = _controller()
    exe = TeachingClassroomActionExecutor(controller=ctl, runtime=runtime)
    actions = [
        TeachingAssistantAction(
            action_id="t1", tool_id="classroom.timer.start", label="Bấm giờ",
            action_class=AIActionClass.MUTATING, arguments={"seconds": 20}, requires_teacher_confirmation=True,
        ),
        TeachingAssistantAction(
            action_id="q1", tool_id="classroom.quiz.display", label="Hiển thị câu hỏi",
            action_class=AIActionClass.MUTATING, arguments={"question": "Tính 2+2"}, requires_teacher_confirmation=True,
        ),
        TeachingAssistantAction(
            action_id="w1", tool_id="classroom.whiteboard.show", label="Hiển thị bảng",
            action_class=AIActionClass.MUTATING, arguments={"title": "Gợi ý", "content": "2 + 2 = ?"}, requires_teacher_confirmation=True,
        ),
    ]
    for action in actions:
        result = exe.execute(action, teacher_confirmed=True)
        assert result.status is ClassroomExecutionStatus.EXECUTED
    runtime_state = runtime.read_status()
    assert runtime_state["timer"]["seconds"] == 20
    assert runtime_state["quiz"]["question"] == "Tính 2+2"
    assert runtime_state["whiteboard"]["content"] == "2 + 2 = ?"


def test_runtime_overlay_contains_live_classroom_controls():
    html = build_runtime_overlay_html(
        {
            "timer": {"status": "running", "seconds": 30, "started_at": "2026-10-02T10:00:00+00:00"},
            "quiz": {"question": "Tính 2+2"},
            "whiteboard": {"title": "Gợi ý", "content": "2+2"},
            "stage": {"content_id": "tool-1", "title": "Sân khấu"},
        },
        {"tool-1": b"<html><body>stage</body></html>"},
    )
    assert 'id="ta-runtime-timer"' in html
    assert "Tính 2+2" in html
    assert "Gợi ý" in html
    assert "srcdoc=\"&lt;html&gt;" in html
