from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from .contracts import AIActionClass
from .governance import AdminPolicyError
from .teaching_assistant import TeachingAssistantAction, TeachingAssistantMode


class ClassroomPhase(str, Enum):
    OPENING = "opening"
    NEW_KNOWLEDGE = "new_knowledge"
    PRACTICE = "practice"
    APPLICATION = "application"
    TRANSITION = "transition"
    CLOSING = "closing"


class TeachingRunState(str, Enum):
    READY = "ready"
    RUNNING = "running"
    WAITING_TEACHER = "waiting_teacher"
    TEACHER_CONTROL = "teacher_control"
    COMPLETED = "completed"
    STOPPED = "stopped"


@dataclass(frozen=True)
class LessonActivityContext:
    lesson_id: str
    activity_id: str
    activity_title: str
    phase: ClassroomPhase
    objective: str = ""
    duration_seconds: int = 0
    selected_slide_id: str = ""
    stage_content_id: str = ""
    question: str = ""
    teacher_notes: str = ""
    allowed_tools: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.lesson_id.strip():
            raise ValueError("lesson_id không được rỗng")
        if not self.activity_id.strip():
            raise ValueError("activity_id không được rỗng")
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds phải >= 0")


@dataclass(frozen=True)
class TeachingScriptLine:
    speaker: str
    text: str
    pause_seconds: float = 0.0
    intent: str = "narrate"


@dataclass(frozen=True)
class ClassroomActionSpec:
    tool_id: str
    label: str
    action_class: AIActionClass
    requires_teacher_confirmation: bool = False
    description: str = ""


@dataclass(frozen=True)
class TeachingActivityPlan:
    plan_id: str
    lesson_id: str
    activity_id: str
    mode: TeachingAssistantMode
    phase: ClassroomPhase
    script: tuple[TeachingScriptLine, ...]
    actions: tuple[TeachingAssistantAction, ...] = ()
    requires_teacher_confirmation: bool = True
    state: TeachingRunState = TeachingRunState.READY
    metadata: Mapping[str, Any] = field(default_factory=dict)


class TeachingClassroomOrchestrator:
    """Deterministic classroom-plan builder for the AI Teaching Assistant.

    The LLM may propose wording or candidate steps later, but this class remains
    the final validator for scope: activity context, allowed tools, action class,
    and teacher override are checked before a plan is created.
    """

    DEFAULT_ACTIONS: tuple[ClassroomActionSpec, ...] = (
        ClassroomActionSpec(
            "classroom.status.read",
            "Đọc trạng thái lớp",
            AIActionClass.READ_ONLY,
            False,
            "Đọc trạng thái vận hành hiện tại.",
        ),
        ClassroomActionSpec(
            "classroom.slide.open",
            "Mở slide bài giảng",
            AIActionClass.MUTATING,
            True,
            "Chọn và đưa nội dung slide lên vùng trình chiếu.",
        ),
        ClassroomActionSpec(
            "classroom.stage.show",
            "Hiển thị sân khấu",
            AIActionClass.MUTATING,
            True,
            "Chuyển nội dung lên sân khấu lớp học.",
        ),
        ClassroomActionSpec(
            "classroom.timer.start",
            "Bắt đầu thời gian hoạt động",
            AIActionClass.MUTATING,
            True,
            "Khởi động bộ đếm thời gian cho hoạt động.",
        ),
        ClassroomActionSpec(
            "classroom.timer.stop",
            "Dừng thời gian hoạt động",
            AIActionClass.MUTATING,
            True,
            "Dừng bộ đếm thời gian.",
        ),
        ClassroomActionSpec(
            "classroom.quiz.display",
            "Hiển thị câu hỏi",
            AIActionClass.MUTATING,
            True,
            "Đưa câu hỏi đã được chuẩn bị lên giao diện lớp học.",
        ),
        ClassroomActionSpec(
            "classroom.whiteboard.show",
            "Hiển thị bảng",
            AIActionClass.MUTATING,
            True,
            "Mở nội dung bảng/trang bảng đã chuẩn bị.",
        ),
        ClassroomActionSpec(
            "classroom.surface.clear_overlays",
            "Làm sạch lớp phủ hoạt động",
            AIActionClass.MUTATING,
            True,
            "Ẩn câu hỏi, bảng và sân khấu của hoạt động trước khi chuyển hoạt động.",
        ),
    )

    def __init__(self, action_specs: Sequence[ClassroomActionSpec] | None = None) -> None:
        source = tuple(action_specs or self.DEFAULT_ACTIONS)
        self._actions = {item.tool_id: item for item in source}

    def _check_tool(self, tool_id: str, context: LessonActivityContext) -> ClassroomActionSpec:
        if context.allowed_tools and tool_id not in context.allowed_tools:
            raise AdminPolicyError(f"Tool chưa được cấp cho hoạt động: {tool_id}")
        try:
            return self._actions[tool_id]
        except KeyError as exc:
            raise AdminPolicyError(f"Classroom action chưa được đăng ký: {tool_id}") from exc

    def build_plan(
        self,
        *,
        context: LessonActivityContext,
        mode: TeachingAssistantMode,
        include_timer: bool = False,
        include_slide: bool = False,
        include_quiz: bool = False,
        include_stage: bool = False,
        include_whiteboard: bool = False,
        clear_overlays: bool = False,
    ) -> TeachingActivityPlan:
        context.validate()
        if mode not in {
            TeachingAssistantMode.MC,
            TeachingAssistantMode.TECHNICAL_OPERATOR,
            TeachingAssistantMode.ACTIVITY_FACILITATOR,
            TeachingAssistantMode.CO_TEACHER,
        }:
            raise AdminPolicyError(f"Mode trợ giảng chưa được hỗ trợ: {mode.value}")

        actions: list[TeachingAssistantAction] = []
        if clear_overlays:
            spec = self._check_tool("classroom.surface.clear_overlays", context)
            actions.append(
                TeachingAssistantAction(
                    action_id=f"action_clear_{context.activity_id}",
                    tool_id=spec.tool_id,
                    label=spec.label,
                    action_class=spec.action_class,
                    arguments={},
                    requires_teacher_confirmation=spec.requires_teacher_confirmation,
                )
            )
        if include_slide:
            spec = self._check_tool("classroom.slide.open", context)
            actions.append(
                TeachingAssistantAction(
                    action_id=f"action_slide_{context.activity_id}",
                    tool_id=spec.tool_id,
                    label=spec.label,
                    action_class=spec.action_class,
                    arguments={"slide_id": context.selected_slide_id},
                    requires_teacher_confirmation=spec.requires_teacher_confirmation,
                )
            )
        if include_quiz:
            spec = self._check_tool("classroom.quiz.display", context)
            actions.append(
                TeachingAssistantAction(
                    action_id=f"action_quiz_{context.activity_id}",
                    tool_id=spec.tool_id,
                    label=spec.label,
                    action_class=spec.action_class,
                    arguments={"question": context.question},
                    requires_teacher_confirmation=spec.requires_teacher_confirmation,
                )
            )
        if include_stage:
            spec = self._check_tool("classroom.stage.show", context)
            actions.append(
                TeachingAssistantAction(
                    action_id=f"action_stage_{context.activity_id}",
                    tool_id=spec.tool_id,
                    label=spec.label,
                    action_class=spec.action_class,
                    arguments={"content_id": context.stage_content_id, "title": context.activity_title},
                    requires_teacher_confirmation=spec.requires_teacher_confirmation,
                )
            )
        if include_whiteboard:
            spec = self._check_tool("classroom.whiteboard.show", context)
            actions.append(
                TeachingAssistantAction(
                    action_id=f"action_whiteboard_{context.activity_id}",
                    tool_id=spec.tool_id,
                    label=spec.label,
                    action_class=spec.action_class,
                    arguments={
                        "title": context.activity_title,
                        "content": context.question or context.objective or "Bảng hoạt động do giáo viên xác nhận.",
                    },
                    requires_teacher_confirmation=spec.requires_teacher_confirmation,
                )
            )
        if include_timer and context.duration_seconds > 0:
            spec = self._check_tool("classroom.timer.start", context)
            actions.append(
                TeachingAssistantAction(
                    action_id=f"action_timer_{context.activity_id}",
                    tool_id=spec.tool_id,
                    label=spec.label,
                    action_class=spec.action_class,
                    arguments={"seconds": context.duration_seconds},
                    requires_teacher_confirmation=spec.requires_teacher_confirmation,
                )
            )

        script = self._build_script(context=context, mode=mode, include_timer=include_timer)
        return TeachingActivityPlan(
            plan_id=f"teachplan_{context.lesson_id}_{context.activity_id}",
            lesson_id=context.lesson_id,
            activity_id=context.activity_id,
            mode=mode,
            phase=context.phase,
            script=script,
            actions=tuple(actions),
            requires_teacher_confirmation=any(a.requires_teacher_confirmation for a in actions),
            metadata={"duration_seconds": context.duration_seconds},
        )

    @staticmethod
    def _build_script(
        *, context: LessonActivityContext, mode: TeachingAssistantMode, include_timer: bool
    ) -> tuple[TeachingScriptLine, ...]:
        title = context.activity_title.strip()
        opening = (
            "Xin chào các em. Chúng ta cùng bắt đầu hoạt động "
            + title
            + "."
        )
        lines: list[TeachingScriptLine] = [
            TeachingScriptLine("AI Trợ giảng", opening, pause_seconds=0.4, intent="opening"),
        ]
        if context.objective:
            lines.append(
                TeachingScriptLine(
                    "AI Trợ giảng",
                    f"Mục tiêu của hoạt động là: {context.objective.strip()}.",
                    pause_seconds=0.5,
                    intent="objective",
                )
            )
        if context.question:
            lines.append(
                TeachingScriptLine(
                    "AI Trợ giảng",
                    f"Câu hỏi dành cho các em: {context.question.strip()}",
                    pause_seconds=0.7,
                    intent="question",
                )
            )
        if include_timer and context.duration_seconds > 0:
            seconds = context.duration_seconds
            lines.append(
                TeachingScriptLine(
                    "AI Trợ giảng",
                    f"Các em có {seconds} giây. Khi sẵn sàng, chúng ta bắt đầu.",
                    pause_seconds=0.4,
                    intent="timer_start",
                )
            )
        if mode is TeachingAssistantMode.MC:
            lines.append(
                TeachingScriptLine(
                    "AI Trợ giảng",
                    "Sau hoạt động, cô/thầy sẽ cùng chúng ta tổng kết và chuyển sang bước tiếp theo.",
                    pause_seconds=0.4,
                    intent="transition",
                )
            )
        return tuple(lines)


__all__ = [
    "ClassroomActionSpec",
    "ClassroomPhase",
    "LessonActivityContext",
    "TeachingActivityPlan",
    "TeachingClassroomOrchestrator",
    "TeachingRunState",
    "TeachingScriptLine",
]
