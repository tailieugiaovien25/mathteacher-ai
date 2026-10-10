from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, MutableMapping, Protocol

from .contracts import AIActionClass
from .governance import AdminPolicyError
from .teaching_assistant import TeachingAssistantAction, TeachingAssistantController


class ClassroomExecutionStatus(str, Enum):
    EXECUTED = "executed"
    TEACHER_CONFIRMATION_REQUIRED = "teacher_confirmation_required"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass(frozen=True)
class ClassroomExecutionResult:
    action_id: str
    tool_id: str
    status: ClassroomExecutionStatus
    message: str
    output: Any = None
    executed_at: str = ""


@dataclass(frozen=True)
class ClassroomRuntimeEvent:
    tool_id: str
    action_id: str
    arguments: Mapping[str, Any]
    created_at: str
    source: str = "ai_teaching_assistant"


class ClassroomRuntimePort(Protocol):
    def execute(self, action: TeachingAssistantAction) -> Any: ...
    def read_status(self) -> Mapping[str, Any]: ...


@dataclass
class InMemoryClassroomRuntime:
    """Deterministic runtime used by tests and non-UI deployments."""

    events: list[ClassroomRuntimeEvent] = field(default_factory=list)
    state: MutableMapping[str, Any] = field(default_factory=dict)

    def execute(self, action: TeachingAssistantAction) -> Any:
        event = ClassroomRuntimeEvent(
            tool_id=action.tool_id,
            action_id=action.action_id,
            arguments=dict(action.arguments),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.events.append(event)
        if action.tool_id == "classroom.status.read":
            return self.read_status()
        self.state[action.tool_id] = dict(action.arguments)
        return {"accepted": True, "tool_id": action.tool_id, "arguments": dict(action.arguments)}

    def read_status(self) -> Mapping[str, Any]:
        return dict(self.state)


class StreamlitClassroomRuntime:
    """Thin adapter that publishes approved classroom actions to Streamlit session state.

    It deliberately does not import Streamlit at module import time. Existing lesson
    surfaces can consume these state keys without changing the AI Kernel.
    """

    EVENT_KEY = "ta_classroom_runtime_event_v13k"
    STATE_KEY = "ta_classroom_runtime_state_v13k"
    LEGACY_EVENT_KEY = "ta_classroom_runtime_event_v13j"
    LEGACY_STATE_KEY = "ta_classroom_runtime_state_v13j"

    def __init__(self, session_state: MutableMapping[str, Any]) -> None:
        self.session_state = session_state

    def _emit(self, action: TeachingAssistantAction) -> ClassroomRuntimeEvent:
        event = ClassroomRuntimeEvent(
            tool_id=action.tool_id,
            action_id=action.action_id,
            arguments=dict(action.arguments),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        payload = {
            "tool_id": event.tool_id,
            "action_id": event.action_id,
            "arguments": dict(event.arguments),
            "created_at": event.created_at,
            "source": event.source,
        }
        self.session_state[self.EVENT_KEY] = payload
        self.session_state[self.LEGACY_EVENT_KEY] = payload
        return event

    def execute(self, action: TeachingAssistantAction) -> Any:
        event = self._emit(action)
        state = dict(self.session_state.get(self.STATE_KEY, {}))
        args = dict(action.arguments)

        if action.tool_id == "classroom.slide.open":
            slide_id = str(args.get("slide_id", "")).strip()
            if not slide_id:
                raise ValueError("slide_id là bắt buộc để mở slide.")
            known_ids = {str(item) for item in self.session_state.get("lesson_slide_ids", ())}
            if known_ids and slide_id not in known_ids:
                raise ValueError("slide_id không thuộc bài giảng hiện tại.")
            # Existing Lesson Designer contract used by the shared surface.
            self.session_state["lesson_slide_selected"] = slide_id
            self.session_state.pop("lesson_surface_index", None)
            state["selected_slide_id"] = slide_id

        elif action.tool_id == "classroom.stage.show":
            content_id = str(args.get("content_id", "")).strip()
            if not content_id:
                raise ValueError("content_id là bắt buộc để hiển thị sân khấu.")
            staged = self.session_state.get("lesson_integrated_stages", {})
            if staged and content_id not in staged:
                raise ValueError("Sân khấu chưa được chuẩn bị cho nội dung đã chọn.")
            state["stage"] = {"content_id": content_id, "title": str(args.get("title", ""))}

        elif action.tool_id == "classroom.timer.start":
            seconds = int(args.get("seconds", 0))
            if seconds <= 0:
                raise ValueError("seconds phải > 0 để bắt đầu timer.")
            state["timer"] = {
                "status": "running",
                "seconds": seconds,
                "started_at": event.created_at,
            }

        elif action.tool_id == "classroom.timer.stop":
            state["timer"] = {"status": "stopped", "stopped_at": event.created_at}

        elif action.tool_id == "classroom.quiz.display":
            question = str(args.get("question", "")).strip()
            if not question:
                raise ValueError("question là bắt buộc để hiển thị câu hỏi.")
            state["quiz"] = {"question": question}

        elif action.tool_id == "classroom.whiteboard.show":
            state["whiteboard"] = {
                "title": str(args.get("title", "")),
                "content": str(args.get("content", "")),
            }

        elif action.tool_id == "classroom.surface.clear_overlays":
            state.pop("stage", None)
            state.pop("quiz", None)
            state.pop("whiteboard", None)

        elif action.tool_id == "classroom.status.read":
            return self.read_status()

        else:
            raise AdminPolicyError(f"Classroom runtime chưa có adapter cho tool: {action.tool_id}")

        self.session_state[self.STATE_KEY] = state
        self.session_state[self.LEGACY_STATE_KEY] = state
        return {"accepted": True, "event": self.session_state[self.EVENT_KEY], "state": state}

    def read_status(self) -> Mapping[str, Any]:
        return dict(self.session_state.get(self.STATE_KEY) or self.session_state.get(self.LEGACY_STATE_KEY, {}))


class TeachingClassroomActionExecutor:
    """Teacher-in-the-loop executor for Classroom Actions.

    ADMIN owns the registered tools and policy. The teacher may explicitly confirm
    an individual classroom action within the active teaching session; the teacher
    never gains permission to change the AI Kernel, tool registry, or governance.
    """

    def __init__(self, *, controller: TeachingAssistantController, runtime: ClassroomRuntimePort) -> None:
        self.controller = controller
        self.runtime = runtime

    def execute(self, action: TeachingAssistantAction, *, teacher_confirmed: bool = False) -> ClassroomExecutionResult:
        try:
            if self.controller.session.teacher_control:
                return ClassroomExecutionResult(
                    action_id=action.action_id,
                    tool_id=action.tool_id,
                    status=ClassroomExecutionStatus.BLOCKED,
                    message="Giáo viên đang giữ quyền điều khiển; Trợ giảng không được thực thi action.",
                )

            self.controller.policy.check_action(action)

            if action.action_class in self.controller.policy.teacher_confirmation_classes:
                if not teacher_confirmed:
                    return ClassroomExecutionResult(
                        action_id=action.action_id,
                        tool_id=action.tool_id,
                        status=ClassroomExecutionStatus.TEACHER_CONFIRMATION_REQUIRED,
                        message="Hành động cần giáo viên xác nhận trực tiếp.",
                    )
                self.controller.approve_action(action.action_id)

            output = self.runtime.execute(action)
            return ClassroomExecutionResult(
                action_id=action.action_id,
                tool_id=action.tool_id,
                status=ClassroomExecutionStatus.EXECUTED,
                message="Classroom Action đã được thực thi theo policy.",
                output=output,
                executed_at=datetime.now(timezone.utc).isoformat(),
            )
        except AdminPolicyError as exc:
            return ClassroomExecutionResult(
                action_id=action.action_id,
                tool_id=action.tool_id,
                status=ClassroomExecutionStatus.REJECTED,
                message=str(exc),
            )
        except Exception as exc:
            return ClassroomExecutionResult(
                action_id=action.action_id,
                tool_id=action.tool_id,
                status=ClassroomExecutionStatus.FAILED,
                message=f"Classroom runtime lỗi: {exc}",
            )


__all__ = [
    "ClassroomExecutionResult",
    "ClassroomExecutionStatus",
    "ClassroomRuntimeEvent",
    "ClassroomRuntimePort",
    "InMemoryClassroomRuntime",
    "StreamlitClassroomRuntime",
    "TeachingClassroomActionExecutor",
]
