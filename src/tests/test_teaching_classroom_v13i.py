import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from ai_kernel.contracts import AIActionClass
from ai_kernel.governance import AdminPolicyError
from ai_kernel.teaching_assistant import TeachingAssistantMode
from ai_kernel.teaching_classroom import (
    ClassroomPhase,
    LessonActivityContext,
    TeachingClassroomOrchestrator,
)
from ai_kernel.agent_runtime import AIToolRegistry, default_ai_tools
from ai_kernel.skills import default_ai_skills


def make_context(**kwargs):
    base = dict(
        lesson_id="l1",
        activity_id="a1",
        activity_title="Khởi động",
        phase=ClassroomPhase.OPENING,
        objective="Ôn kiến thức cũ",
        duration_seconds=60,
        selected_slide_id="slide-1",
        question="Tính 2+3 bằng bao nhiêu?",
        allowed_tools=(
            "classroom.status.read",
            "classroom.slide.open",
            "classroom.timer.start",
            "classroom.quiz.display",
        ),
    )
    base.update(kwargs)
    return LessonActivityContext(**base)


def test_orchestrator_builds_mc_script_and_actions():
    plan = TeachingClassroomOrchestrator().build_plan(
        context=make_context(),
        mode=TeachingAssistantMode.MC,
        include_timer=True,
        include_slide=True,
        include_quiz=True,
    )
    assert plan.mode is TeachingAssistantMode.MC
    assert len(plan.script) >= 3
    assert [a.tool_id for a in plan.actions] == [
        "classroom.slide.open",
        "classroom.quiz.display",
        "classroom.timer.start",
    ]
    assert plan.requires_teacher_confirmation is True


def test_disallowed_tool_is_blocked_by_activity_context():
    context = make_context(allowed_tools=("classroom.status.read",))
    with pytest.raises(AdminPolicyError):
        TeachingClassroomOrchestrator().build_plan(
            context=context,
            mode=TeachingAssistantMode.TECHNICAL_OPERATOR,
            include_timer=True,
        )


def test_classroom_tools_are_registered_and_risky_tools_require_approval():
    registry = AIToolRegistry(default_ai_tools())
    slide = registry.resolve("classroom.slide.open")
    timer = registry.resolve("classroom.timer.start")
    status = registry.resolve("classroom.status.read")
    assert AIActionClass.MUTATING in slide.allowed_actions
    assert slide.requires_admin_approval is True
    assert timer.requires_admin_approval is True
    assert AIActionClass.READ_ONLY in status.allowed_actions


def test_classroom_orchestrator_skill_is_registered():
    skills = {s.skill_id: s for s in default_ai_skills()}
    skill = skills["classroom.teaching.orchestrator"]
    assert skill.admin_enabled is True
    assert AIActionClass.ADVISORY in skill.allowed_actions
    assert AIActionClass.MUTATING in skill.allowed_actions
