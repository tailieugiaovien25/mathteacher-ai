import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from ai_kernel.contracts import AIActionClass
from ai_kernel.governance import AdminPolicyError
from ai_kernel.teaching_assistant import (
    TeachingAssistantAction,
    TeachingAssistantController,
    TeachingAssistantMode,
    TeachingAssistantTurn,
    TeachingPersonaProfile,
    default_teaching_personas,
    default_teaching_policy,
)


def test_default_persona_supports_mc_and_technical_modes():
    persona = default_teaching_personas()[0]
    assert TeachingAssistantMode.MC in persona.allowed_modes
    assert TeachingAssistantMode.TECHNICAL_OPERATOR in persona.allowed_modes


def test_read_only_classroom_action_is_allowed():
    persona = default_teaching_personas()[0]
    controller = TeachingAssistantController(
        persona=persona,
        policy=default_teaching_policy(persona.persona_id),
    )
    actions = controller.propose_actions([
        TeachingAssistantAction(
            action_id="a1",
            tool_id="classroom.status.read",
            label="Đọc trạng thái lớp",
            action_class=AIActionClass.READ_ONLY,
        )
    ])
    assert actions[0].tool_id == "classroom.status.read"


def test_mutating_action_requires_teacher_confirmation():
    persona = default_teaching_personas()[0]
    controller = TeachingAssistantController(
        persona=persona,
        policy=default_teaching_policy(persona.persona_id),
    )
    with pytest.raises(AdminPolicyError):
        controller.propose_actions([
            TeachingAssistantAction(
                action_id="a2",
                tool_id="classroom.slide.open",
                label="Mở slide",
                action_class=AIActionClass.MUTATING,
                requires_teacher_confirmation=False,
            )
        ])


def test_teacher_can_take_control_immediately():
    persona = default_teaching_personas()[0]
    controller = TeachingAssistantController(
        persona=persona,
        policy=default_teaching_policy(persona.persona_id),
    )
    session = controller.teacher_take_control()
    assert session.teacher_control is True
    assert session.turn == TeachingAssistantTurn.TEACHER_CONTROL
    assert controller.propose_actions([]) == ()


def test_teacher_can_release_and_stop():
    persona = TeachingPersonaProfile(
        persona_id="p1",
        display_name="Trợ giảng",
        role="AI trợ giảng",
    )
    controller = TeachingAssistantController(
        persona=persona,
        policy=default_teaching_policy("p1"),
    )
    controller.teacher_take_control()
    assert controller.teacher_release_control().teacher_control is False
    assert controller.stop().turn == TeachingAssistantTurn.STOPPED
