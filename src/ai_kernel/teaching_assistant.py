from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence
from uuid import uuid4

from .contracts import AIActionClass, AIOwnership
from .governance import AdminPolicyError


class TeachingAssistantMode(str, Enum):
    CO_TEACHER = "co_teacher"
    MC = "mc"
    TECHNICAL_OPERATOR = "technical_operator"
    ACTIVITY_FACILITATOR = "activity_facilitator"


class TeachingAssistantTurn(str, Enum):
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"
    TEACHER_CONTROL = "teacher_control"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass(frozen=True)
class TeachingPersonaProfile:
    persona_id: str
    display_name: str
    role: str
    language: str = "vi-VN"
    allowed_modes: tuple[TeachingAssistantMode, ...] = (
        TeachingAssistantMode.CO_TEACHER,
    )
    voice_profile_id: str = "default-vietnamese"
    avatar_profile_id: str = "default-avatar"
    speaking_style: str = "rõ ràng, thân thiện, phù hợp lớp học"
    teacher_override_enabled: bool = True


@dataclass(frozen=True)
class TeachingAssistantAction:
    action_id: str
    tool_id: str
    label: str
    action_class: AIActionClass
    arguments: Mapping[str, Any] = field(default_factory=dict)
    requires_teacher_confirmation: bool = False


@dataclass(frozen=True)
class TeachingAssistantPolicy:
    persona_id: str
    owner: AIOwnership
    allowed_tool_ids: tuple[str, ...] = ()
    max_actions_per_turn: int = 4
    auto_action_classes: tuple[AIActionClass, ...] = (
        AIActionClass.READ_ONLY,
        AIActionClass.ADVISORY,
    )
    teacher_confirmation_classes: tuple[AIActionClass, ...] = (
        AIActionClass.MUTATING,
        AIActionClass.GOVERNANCE,
    )
    teacher_can_interrupt: bool = True

    def check_action(self, action: TeachingAssistantAction) -> None:
        if self.allowed_tool_ids and action.tool_id not in self.allowed_tool_ids:
            raise AdminPolicyError(f"Tool chưa được cấp cho trợ giảng: {action.tool_id}")
        if action.action_class in self.teacher_confirmation_classes:
            if not action.requires_teacher_confirmation:
                raise AdminPolicyError(
                    f"Hành động {action.tool_id} phải yêu cầu giáo viên xác nhận."
                )
        elif action.action_class in self.auto_action_classes:
            return
        else:
            raise AdminPolicyError(
                f"Action class chưa được policy trợ giảng cho phép: {action.action_class.value}"
            )


@dataclass(frozen=True)
class TeachingAssistantSession:
    session_id: str
    persona_id: str
    mode: TeachingAssistantMode
    turn: TeachingAssistantTurn = TeachingAssistantTurn.LISTENING
    teacher_control: bool = False
    approved_action_ids: tuple[str, ...] = ()


class TeachingAssistantController:
    """Policy boundary for future STT/TTS/avatar adapters.

    The controller is deliberately UI/model agnostic. It validates proposed
    classroom actions before they can reach the existing Safe Agent Runtime.
    Voice, avatar, WebRTC, and classroom tools remain replaceable adapters.
    """

    def __init__(self, *, persona: TeachingPersonaProfile, policy: TeachingAssistantPolicy) -> None:
        if persona.persona_id != policy.persona_id:
            raise ValueError("persona_id và policy.persona_id phải khớp")
        self.persona = persona
        self.policy = policy
        self.session = TeachingAssistantSession(
            session_id="ta_" + uuid4().hex,
            persona_id=persona.persona_id,
            mode=TeachingAssistantMode.CO_TEACHER,
        )

    def propose_actions(self, actions: Sequence[TeachingAssistantAction]) -> tuple[TeachingAssistantAction, ...]:
        if self.session.teacher_control:
            return ()
        limited = tuple(actions)[: self.policy.max_actions_per_turn]
        for action in limited:
            self.policy.check_action(action)
        return limited

    def approve_action(self, action_id: str) -> TeachingAssistantSession:
        """Record an individually teacher-approved classroom action.

        This does not change Kernel/Governance permissions; it only records that
        the currently signed-in teacher confirmed the specific action instance.
        """
        if not isinstance(action_id, str) or not action_id.strip():
            raise ValueError("action_id không được rỗng")
        if self.session.teacher_control:
            raise AdminPolicyError("Giáo viên đang giữ quyền điều khiển; không phê duyệt action cho AI.")
        approved = tuple(dict.fromkeys((*self.session.approved_action_ids, action_id)))
        self.session = TeachingAssistantSession(
            session_id=self.session.session_id,
            persona_id=self.session.persona_id,
            mode=self.session.mode,
            turn=self.session.turn,
            teacher_control=self.session.teacher_control,
            approved_action_ids=approved,
        )
        return self.session

    def teacher_take_control(self) -> TeachingAssistantSession:
        self.session = TeachingAssistantSession(
            session_id=self.session.session_id,
            persona_id=self.session.persona_id,
            mode=self.session.mode,
            turn=TeachingAssistantTurn.TEACHER_CONTROL,
            teacher_control=True,
            approved_action_ids=self.session.approved_action_ids,
        )
        return self.session

    def teacher_release_control(self) -> TeachingAssistantSession:
        self.session = TeachingAssistantSession(
            session_id=self.session.session_id,
            persona_id=self.session.persona_id,
            mode=self.session.mode,
            turn=TeachingAssistantTurn.LISTENING,
            teacher_control=False,
            approved_action_ids=self.session.approved_action_ids,
        )
        return self.session

    def stop(self) -> TeachingAssistantSession:
        self.session = TeachingAssistantSession(
            session_id=self.session.session_id,
            persona_id=self.session.persona_id,
            mode=self.session.mode,
            turn=TeachingAssistantTurn.STOPPED,
            teacher_control=True,
            approved_action_ids=self.session.approved_action_ids,
        )
        return self.session


def default_teaching_personas() -> tuple[TeachingPersonaProfile, ...]:
    return (
        TeachingPersonaProfile(
            persona_id="math_assistant_female_vi",
            display_name="Trợ giảng Toán",
            role="AI trợ giảng môn Toán THCS",
            allowed_modes=(
                TeachingAssistantMode.CO_TEACHER,
                TeachingAssistantMode.MC,
                TeachingAssistantMode.TECHNICAL_OPERATOR,
                TeachingAssistantMode.ACTIVITY_FACILITATOR,
            ),
        ),
    )


def default_teaching_policy(persona_id: str) -> TeachingAssistantPolicy:
    return TeachingAssistantPolicy(
        persona_id=persona_id,
        owner=AIOwnership.SYSTEM,
        allowed_tool_ids=(
            "classroom.slide.open",
            "classroom.stage.show",
            "classroom.timer.start",
            "classroom.timer.stop",
            "classroom.quiz.display",
            "classroom.whiteboard.show",
            "classroom.status.read",
            "classroom.surface.clear_overlays",
        ),
    )
