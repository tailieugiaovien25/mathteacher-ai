from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, MutableSequence, Sequence
from uuid import uuid4

from .governance import AdminPolicyError
from .teaching_assistant import TeachingAssistantController, TeachingAssistantMode
from .teaching_classroom import LessonActivityContext, TeachingActivityPlan, TeachingRunState
from .teaching_classroom_executor import (
    ClassroomExecutionResult,
    ClassroomExecutionStatus,
    TeachingClassroomActionExecutor,
)


class TeachingSessionStatus(str, Enum):
    PREPARING = "preparing"
    RUNNING = "running"
    WAITING_TEACHER = "waiting_teacher"
    TEACHER_CONTROL = "teacher_control"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"


@dataclass(frozen=True)
class TeachingSessionEvent:
    event_id: str
    session_id: str
    kind: str
    created_at: str
    activity_id: str = ""
    phase: str = ""
    action_id: str = ""
    tool_id: str = ""
    status: str = ""
    message: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TeachingSessionSnapshot:
    session_id: str
    lesson_id: str
    status: TeachingSessionStatus
    activity_index: int
    total_activities: int
    current_activity_id: str
    current_phase: str
    teacher_control: bool
    started_at: str
    updated_at: str
    completed_at: str = ""
    last_action_id: str = ""
    last_tool_id: str = ""
    last_message: str = ""
    event_count: int = 0


class TeachingSessionManager:
    """State machine for one live MathTeacher AI lesson session.

    This layer owns the *teaching session*, not AI governance. Model/provider,
    skill registry, tool registry and admin policy remain outside and continue
    to be enforced by the existing Kernel/TeachingAssistantController.
    """

    def __init__(
        self,
        *,
        controller: TeachingAssistantController,
        executor: TeachingClassroomActionExecutor,
        max_activities: int = 32,
    ) -> None:
        if max_activities <= 0:
            raise ValueError("max_activities phải > 0")
        self.controller = controller
        self.executor = executor
        self.max_activities = max_activities
        self.session_id = "teachsession_" + uuid4().hex
        self._lesson_id = ""
        self._activities: tuple[LessonActivityContext, ...] = ()
        self._current_index = -1
        self._status = TeachingSessionStatus.PREPARING
        self._status_before_teacher_control: TeachingSessionStatus | None = None
        self._started_at = ""
        self._updated_at = self._now()
        self._completed_at = ""
        self._events: list[TeachingSessionEvent] = []
        self._last_action_id = ""
        self._last_tool_id = ""
        self._last_message = ""

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @property
    def activities(self) -> tuple[LessonActivityContext, ...]:
        return self._activities

    @property
    def current_activity(self) -> LessonActivityContext | None:
        if 0 <= self._current_index < len(self._activities):
            return self._activities[self._current_index]
        return None

    @property
    def status(self) -> TeachingSessionStatus:
        return self._status

    def start(self, *, lesson_id: str, activities: Sequence[LessonActivityContext]) -> TeachingSessionSnapshot:
        if self._status is not TeachingSessionStatus.PREPARING:
            raise AdminPolicyError("Teaching session hiện tại chưa thể khởi động lại; hãy tạo session mới.")
        if not lesson_id.strip():
            raise ValueError("lesson_id không được rỗng")
        source = tuple(activities)
        if not source:
            raise ValueError("Phải có ít nhất một activity để bắt đầu tiết dạy.")
        if len(source) > self.max_activities:
            raise ValueError(f"Số activity vượt giới hạn {self.max_activities}.")
        for activity in source:
            activity.validate()
            if activity.lesson_id != lesson_id:
                raise ValueError("Tất cả activity phải thuộc cùng lesson_id.")
        self._lesson_id = lesson_id
        self._activities = source
        self._current_index = 0
        self._status = TeachingSessionStatus.RUNNING
        self._status_before_teacher_control = None
        self._started_at = self._now()
        self._completed_at = ""
        self._last_action_id = self._last_tool_id = self._last_message = ""
        self._record("session.started", message="Bắt đầu phiên dạy.")
        self._record_current("activity.entered", message="Bắt đầu activity đầu tiên.")
        return self.snapshot()

    def build_plan(
        self,
        orchestrator: Any,
        *,
        mode: TeachingAssistantMode,
        include_timer: bool = False,
        include_slide: bool = False,
        include_quiz: bool = False,
        include_stage: bool = False,
        include_whiteboard: bool = False,
        clear_overlays: bool = True,
    ) -> TeachingActivityPlan:
        context = self._require_current_activity()
        if self._status is not TeachingSessionStatus.RUNNING:
            raise AdminPolicyError("Chỉ có thể lập kế hoạch khi phiên dạy đang RUNNING.")
        return orchestrator.build_plan(
            context=context,
            mode=mode,
            include_timer=include_timer,
            include_slide=include_slide,
            include_quiz=include_quiz,
            include_stage=include_stage,
            include_whiteboard=include_whiteboard,
            clear_overlays=clear_overlays,
        )

    def execute_plan(
        self,
        plan: TeachingActivityPlan,
        *,
        teacher_confirmed: bool = False,
    ) -> tuple[ClassroomExecutionResult, ...]:
        current = self._require_current_activity()
        if plan.lesson_id != current.lesson_id or plan.activity_id != current.activity_id:
            raise AdminPolicyError("Teaching plan không thuộc activity hiện tại.")
        if self._status is TeachingSessionStatus.TEACHER_CONTROL:
            self._record_current("plan.blocked", message="Teacher Override đang có hiệu lực.")
            return tuple(
                ClassroomExecutionResult(
                    action_id=a.action_id,
                    tool_id=a.tool_id,
                    status=ClassroomExecutionStatus.BLOCKED,
                    message="Giáo viên đang giữ quyền điều khiển.",
                )
                for a in plan.actions
            )
        if self._status not in {TeachingSessionStatus.RUNNING, TeachingSessionStatus.WAITING_TEACHER}:
            raise AdminPolicyError("Phiên dạy không ở trạng thái có thể thực thi action.")

        results: list[ClassroomExecutionResult] = []
        waiting = False
        for action in plan.actions:
            result = self.executor.execute(action, teacher_confirmed=teacher_confirmed)
            results.append(result)
            self._last_action_id = action.action_id
            self._last_tool_id = action.tool_id
            self._last_message = result.message
            self._updated_at = self._now()
            self._record_current(
                "action.executed" if result.status is ClassroomExecutionStatus.EXECUTED else "action.result",
                action_id=action.action_id,
                tool_id=action.tool_id,
                status=result.status.value,
                message=result.message,
            )
            if result.status is ClassroomExecutionStatus.TEACHER_CONFIRMATION_REQUIRED:
                waiting = True
                break
            if result.status in {ClassroomExecutionStatus.BLOCKED, ClassroomExecutionStatus.REJECTED, ClassroomExecutionStatus.FAILED}:
                break
        if waiting:
            self._status = TeachingSessionStatus.WAITING_TEACHER
        elif results and all(r.status is ClassroomExecutionStatus.EXECUTED for r in results):
            self._status = TeachingSessionStatus.RUNNING
        return tuple(results)

    def advance(self) -> TeachingSessionSnapshot:
        if self._status is TeachingSessionStatus.TEACHER_CONTROL:
            raise AdminPolicyError("Không thể chuyển activity khi giáo viên đang giữ quyền.")
        if self._status not in {TeachingSessionStatus.RUNNING, TeachingSessionStatus.WAITING_TEACHER}:
            raise AdminPolicyError("Phiên dạy chưa ở trạng thái có thể chuyển activity.")
        if self._current_index + 1 >= len(self._activities):
            self.complete()
            return self.snapshot()
        self._current_index += 1
        self._status = TeachingSessionStatus.RUNNING
        self._record_current("activity.entered", message="Chuyển sang activity tiếp theo.")
        return self.snapshot()

    def teacher_take_control(self, *, reason: str = "") -> TeachingSessionSnapshot:
        resumable = {
            TeachingSessionStatus.RUNNING,
            TeachingSessionStatus.WAITING_TEACHER,
            TeachingSessionStatus.PAUSED,
        }
        if self._status not in resumable:
            raise AdminPolicyError("Chỉ có thể giành quyền điều khiển trong một phiên dạy đang hoạt động.")
        self._status_before_teacher_control = self._status
        self.controller.teacher_take_control()
        self._status = TeachingSessionStatus.TEACHER_CONTROL
        self._last_message = reason or "Giáo viên giành quyền điều khiển."
        self._record("teacher.control_taken", message=self._last_message)
        return self.snapshot()

    def teacher_release_control(self) -> TeachingSessionSnapshot:
        if self._status is not TeachingSessionStatus.TEACHER_CONTROL:
            raise AdminPolicyError("Phiên dạy không ở trạng thái giáo viên giữ quyền điều khiển.")
        self.controller.teacher_release_control()
        self._status = self._status_before_teacher_control or TeachingSessionStatus.RUNNING
        self._status_before_teacher_control = None
        self._last_message = "Giáo viên trả quyền điều khiển cho Trợ giảng."
        self._record("teacher.control_released", message=self._last_message)
        return self.snapshot()

    def pause(self, *, reason: str = "") -> TeachingSessionSnapshot:
        if self._status is not TeachingSessionStatus.RUNNING:
            raise AdminPolicyError("Chỉ có thể tạm dừng khi session đang RUNNING.")
        self.controller.pause()
        self._status = TeachingSessionStatus.PAUSED
        self._last_message = reason or "Phiên dạy tạm dừng."
        self._record("session.paused", message=self._last_message)
        return self.snapshot()

    def resume(self) -> TeachingSessionSnapshot:
        if self._status is not TeachingSessionStatus.PAUSED:
            raise AdminPolicyError("Phiên dạy không ở trạng thái PAUSED.")
        self.controller.resume()
        self._status = TeachingSessionStatus.RUNNING
        self._last_message = "Phiên dạy tiếp tục."
        self._record("session.resumed", message=self._last_message)
        return self.snapshot()

    def complete(self) -> TeachingSessionSnapshot:
        if self._status is TeachingSessionStatus.TEACHER_CONTROL:
            raise AdminPolicyError("Không thể kết thúc session khi giáo viên đang giữ quyền.")
        if self._status is TeachingSessionStatus.COMPLETED:
            return self.snapshot()
        self._status = TeachingSessionStatus.COMPLETED
        self._status_before_teacher_control = None
        self._completed_at = self._now()
        self._last_message = "Phiên dạy hoàn thành."
        self._record("session.completed", message=self._last_message)
        return self.snapshot()

    def stop(self, *, reason: str = "") -> TeachingSessionSnapshot:
        self._status = TeachingSessionStatus.STOPPED
        self._status_before_teacher_control = None
        self._completed_at = self._now()
        self._last_message = reason or "Phiên dạy dừng."
        self._record("session.stopped", message=self._last_message)
        return self.snapshot()

    def events(self) -> tuple[TeachingSessionEvent, ...]:
        return tuple(self._events)

    def snapshot(self) -> TeachingSessionSnapshot:
        current = self.current_activity
        return TeachingSessionSnapshot(
            session_id=self.session_id,
            lesson_id=self._lesson_id,
            status=self._status,
            activity_index=self._current_index,
            total_activities=len(self._activities),
            current_activity_id=current.activity_id if current else "",
            current_phase=current.phase.value if current else "",
            teacher_control=self._status is TeachingSessionStatus.TEACHER_CONTROL,
            started_at=self._started_at,
            updated_at=self._updated_at,
            completed_at=self._completed_at,
            last_action_id=self._last_action_id,
            last_tool_id=self._last_tool_id,
            last_message=self._last_message,
            event_count=len(self._events),
        )

    def _require_current_activity(self) -> LessonActivityContext:
        current = self.current_activity
        if current is None:
            raise AdminPolicyError("Phiên dạy chưa có activity hiện tại.")
        return current

    def _record(
        self,
        kind: str,
        *,
        activity_id: str = "",
        phase: str = "",
        action_id: str = "",
        tool_id: str = "",
        status: str = "",
        message: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        self._updated_at = self._now()
        self._events.append(
            TeachingSessionEvent(
                event_id="tse_" + uuid4().hex,
                session_id=self.session_id,
                kind=kind,
                created_at=self._updated_at,
                activity_id=activity_id,
                phase=phase,
                action_id=action_id,
                tool_id=tool_id,
                status=status,
                message=message,
                metadata=dict(metadata or {}),
            )
        )

    def _record_current(self, kind: str, **kwargs: Any) -> None:
        current = self.current_activity
        self._record(
            kind,
            activity_id=current.activity_id if current else "",
            phase=current.phase.value if current else "",
            **kwargs,
        )


__all__ = [
    "TeachingSessionEvent",
    "TeachingSessionManager",
    "TeachingSessionSnapshot",
    "TeachingSessionStatus",
]
