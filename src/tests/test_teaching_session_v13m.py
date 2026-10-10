from __future__ import annotations

import pytest

from ai_kernel.governance import AdminPolicyError
from ai_kernel.teaching_assistant import TeachingAssistantMode, TeachingAssistantController, default_teaching_personas, default_teaching_policy
from ai_kernel.teaching_classroom import ClassroomPhase, LessonActivityContext, TeachingClassroomOrchestrator
from ai_kernel.teaching_classroom_executor import InMemoryClassroomRuntime, TeachingClassroomActionExecutor, ClassroomExecutionStatus
from ai_kernel.teaching_session import TeachingSessionManager, TeachingSessionStatus


def make_manager():
    persona = default_teaching_personas()[0]
    controller = TeachingAssistantController(persona=persona, policy=default_teaching_policy(persona.persona_id))
    runtime = InMemoryClassroomRuntime()
    executor = TeachingClassroomActionExecutor(controller=controller, runtime=runtime)
    return TeachingSessionManager(controller=controller, executor=executor), runtime


def activities():
    return [
        LessonActivityContext(
            lesson_id='lesson-1', activity_id='opening', activity_title='Khởi động', phase=ClassroomPhase.OPENING,
            objective='Kích hoạt kiến thức nền', duration_seconds=30, selected_slide_id='s1', question='Câu hỏi mở đầu',
            allowed_tools=('classroom.surface.clear_overlays','classroom.slide.open','classroom.quiz.display','classroom.timer.start'),
        ),
        LessonActivityContext(
            lesson_id='lesson-1', activity_id='practice', activity_title='Luyện tập', phase=ClassroomPhase.PRACTICE,
            objective='Củng cố', duration_seconds=60, selected_slide_id='s2',
            allowed_tools=('classroom.surface.clear_overlays','classroom.slide.open','classroom.timer.start'),
        ),
        LessonActivityContext(
            lesson_id='lesson-1', activity_id='application', activity_title='Vận dụng', phase=ClassroomPhase.APPLICATION,
            objective='Vận dụng kiến thức', duration_seconds=90, selected_slide_id='s3',
            allowed_tools=('classroom.surface.clear_overlays','classroom.slide.open','classroom.timer.start'),
        ),
    ]


def test_start_and_activity_transition():
    manager, _ = make_manager()
    snap = manager.start(lesson_id='lesson-1', activities=activities())
    assert snap.status is TeachingSessionStatus.RUNNING
    assert snap.current_activity_id == 'opening'
    snap = manager.advance()
    assert snap.current_activity_id == 'practice'
    assert snap.activity_index == 1


def test_build_execute_and_audit():
    manager, runtime = make_manager()
    manager.start(lesson_id='lesson-1', activities=activities())
    plan = manager.build_plan(TeachingClassroomOrchestrator(), mode=TeachingAssistantMode.MC,
                              include_slide=True, include_quiz=True, include_timer=True, clear_overlays=True)
    results = manager.execute_plan(plan, teacher_confirmed=True)
    assert [r.status for r in results] == [ClassroomExecutionStatus.EXECUTED] * 4
    state = runtime.read_status()
    assert state['classroom.slide.open']['slide_id'] == 's1'
    assert state['classroom.quiz.display']['question'] == 'Câu hỏi mở đầu'
    assert state['classroom.timer.start']['seconds'] == 30
    assert all(e.session_id == manager.session_id for e in manager.events())
    assert manager.snapshot().last_tool_id == 'classroom.timer.start'


def test_confirmation_gate_and_retry():
    manager, _ = make_manager()
    manager.start(lesson_id='lesson-1', activities=activities())
    plan = manager.build_plan(TeachingClassroomOrchestrator(), mode=TeachingAssistantMode.TECHNICAL_OPERATOR,
                              include_slide=True, clear_overlays=True)
    results = manager.execute_plan(plan, teacher_confirmed=False)
    assert results[0].status is ClassroomExecutionStatus.TEACHER_CONFIRMATION_REQUIRED
    assert manager.snapshot().status is TeachingSessionStatus.WAITING_TEACHER
    results = manager.execute_plan(plan, teacher_confirmed=True)
    assert all(r.status is ClassroomExecutionStatus.EXECUTED for r in results)
    assert manager.snapshot().status is TeachingSessionStatus.RUNNING


def test_teacher_override_blocks_plan_then_release_resumes():
    manager, _ = make_manager()
    manager.start(lesson_id='lesson-1', activities=activities())
    manager.teacher_take_control(reason='Giáo viên trực tiếp giảng.')
    assert manager.snapshot().status is TeachingSessionStatus.TEACHER_CONTROL
    plan = TeachingClassroomOrchestrator().build_plan(context=activities()[0], mode=TeachingAssistantMode.MC, include_slide=True)
    blocked = manager.execute_plan(plan, teacher_confirmed=True)
    assert blocked[0].status is ClassroomExecutionStatus.BLOCKED
    manager.teacher_release_control()
    assert manager.snapshot().status is TeachingSessionStatus.RUNNING


def test_pause_resume_and_complete():
    manager, _ = make_manager()
    manager.start(lesson_id='lesson-1', activities=activities())
    manager.pause(reason='Tạm dừng để giải thích.')
    assert manager.snapshot().status is TeachingSessionStatus.PAUSED
    manager.resume()
    assert manager.snapshot().status is TeachingSessionStatus.RUNNING
    manager.advance()
    manager.advance()
    manager.advance()
    assert manager.snapshot().status is TeachingSessionStatus.COMPLETED
    assert any(e.kind == 'session.completed' for e in manager.events())


def test_lesson_scope_and_session_lifecycle_are_protected():
    manager, _ = make_manager()
    with pytest.raises(ValueError):
        manager.start(lesson_id='lesson-1', activities=[])
    bad = [activities()[0], LessonActivityContext('other', 'x', 'Sai lesson', ClassroomPhase.PRACTICE)]
    with pytest.raises(ValueError):
        manager.start(lesson_id='lesson-1', activities=bad)
    manager.start(lesson_id='lesson-1', activities=activities())
    manager.stop(reason='Dừng phiên test')
    with pytest.raises(AdminPolicyError):
        manager.start(lesson_id='lesson-1', activities=activities())
