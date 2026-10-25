from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from uuid import uuid4

from .approval_queue import ApprovalQueue
from .contracts import AIActionClass, AIOwnership
from .governance import AdminPolicyError
from .skills import AISkillSpec


class AgentRunStatus(str, Enum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    MAX_STEPS = "max_steps"


class ToolCallStatus(str, Enum):
    EXECUTED = "executed"
    APPROVAL_REQUIRED = "approval_required"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass(frozen=True)
class AIToolSpec:
    tool_id: str
    label: str
    description: str
    allowed_actions: frozenset[AIActionClass]
    capabilities: tuple[str, ...] = ()
    admin_enabled: bool = True
    requires_admin_approval: bool = False


@dataclass(frozen=True)
class AIToolCall:
    tool_id: str
    arguments: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AIToolResult:
    tool_id: str
    status: ToolCallStatus
    output: Any = None
    message: str = ""
    approval_id: str = ""


@dataclass(frozen=True)
class AgentStep:
    step_id: str
    index: int
    tool_id: str
    status: ToolCallStatus
    message: str = ""
    approval_id: str = ""
    created_at: str = ""


@dataclass(frozen=True)
class AgentRun:
    run_id: str
    task_id: str
    skill_id: str
    owner: AIOwnership
    status: AgentRunStatus
    max_steps: int
    steps: tuple[AgentStep, ...] = ()
    created_at: str = ""
    completed_at: str = ""
    audit_id: str = ""


ToolHandler = Callable[[Mapping[str, Any]], Any]


class AIToolRegistry:
    """ADMIN-owned allow-list of tools exposed to agents.

    The registry is deliberately explicit: an agent cannot discover arbitrary
    Python functions, import modules, register a new tool, or escalate a tool's
    action class at runtime.
    """

    def __init__(self, tools: Iterable[AIToolSpec] | None = None) -> None:
        self._specs = {item.tool_id: item for item in (tools or default_ai_tools())}
        self._handlers: dict[str, ToolHandler] = {}

    def specs(self) -> tuple[AIToolSpec, ...]:
        return tuple(self._specs.values())

    def resolve(self, tool_id: str) -> AIToolSpec:
        try:
            spec = self._specs[str(tool_id).strip()]
        except KeyError as exc:
            raise AdminPolicyError(f"Tool chưa được ADMIN đăng ký: {tool_id}") from exc
        if not spec.admin_enabled:
            raise AdminPolicyError(f"Tool chưa được ADMIN bật: {tool_id}")
        return spec

    def bind(self, tool_id: str, handler: ToolHandler) -> None:
        """Bind executable code to an existing ADMIN-approved tool only."""
        spec = self.resolve(tool_id)
        if not callable(handler):
            raise TypeError("Tool handler must be callable")
        self._handlers[spec.tool_id] = handler

    def handler(self, tool_id: str) -> ToolHandler:
        self.resolve(tool_id)
        try:
            return self._handlers[tool_id]
        except KeyError as exc:
            raise RuntimeError(f"Tool chưa được bind runtime handler: {tool_id}") from exc


class JSONAgentRunStore:
    """Local-first audit store for agent runs and approval requests."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = Path(path or os.getenv("MATH_TEACHER_AI_AGENT_RUNS", ".mathteacher_ai/agent_runs.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def _read(self) -> list[dict[str, Any]]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return list(payload) if isinstance(payload, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def _write(self, rows: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix="agent-runs-", suffix=".json", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(rows, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def append(self, run: AgentRun) -> None:
        rows = self._read()
        rows.append(asdict(run) | {"owner": run.owner.value, "status": run.status.value})
        self._write(rows)


class SafeAgentRuntime:
    """Bounded agent executor under ADMIN governance.

    The runtime executes only registered tools. READ_ONLY/ADVISORY calls may
    run automatically; MUTATING/GOVERNANCE calls require ADMIN ownership and,
    when configured, an explicit approval token. The runtime never changes its
    own registry, Kernel, or governance rules.
    """

    def __init__(
        self,
        *,
        skills: Iterable[AISkillSpec],
        tools: AIToolRegistry | None = None,
        store: JSONAgentRunStore | None = None,
        approval_queue: ApprovalQueue | None = None,
        default_max_steps: int = 8,
    ) -> None:
        if default_max_steps < 1:
            raise ValueError("default_max_steps must be >= 1")
        self.skills = {item.skill_id: item for item in skills}
        self.tools = tools or AIToolRegistry()
        self.store = store or JSONAgentRunStore()
        self.approval_queue = approval_queue or ApprovalQueue()
        self.default_max_steps = min(int(default_max_steps), 32)

    def _resolve_skill(self, skill_id: str) -> AISkillSpec:
        try:
            skill = self.skills[skill_id]
        except KeyError as exc:
            raise AdminPolicyError(f"AI skill chưa được ADMIN đăng ký: {skill_id}") from exc
        if not skill.admin_enabled:
            raise AdminPolicyError(f"AI skill chưa được ADMIN bật: {skill_id}")
        return skill

    def _check_action(self, *, skill: AISkillSpec, spec: AIToolSpec, owner: AIOwnership) -> None:
        if not spec.allowed_actions:
            raise AdminPolicyError(f"Tool không có action được phép: {spec.tool_id}")
        if not spec.allowed_actions.intersection(skill.allowed_actions):
            raise AdminPolicyError(f"Tool {spec.tool_id} không phù hợp skill {skill.skill_id}")

    def run(
        self,
        *,
        task_id: str,
        skill_id: str,
        owner: AIOwnership,
        plan: Iterable[AIToolCall],
        max_steps: int | None = None,
        approval_token: str = "",
        approval_id: str = "",
    ) -> AgentRun:
        self._resolve_skill(skill_id)
        bound_limit = self.default_max_steps if max_steps is None else min(max(1, int(max_steps)), 32)
        calls = tuple(plan)
        now = datetime.now(timezone.utc).isoformat()
        run_id = "agent_" + uuid4().hex
        audit_id = "aia_" + uuid4().hex
        steps: list[AgentStep] = []
        status = AgentRunStatus.COMPLETED

        for index, call in enumerate(calls[:bound_limit], start=1):
            spec = self.tools.resolve(call.tool_id)
            skill = self._resolve_skill(skill_id)
            try:
                self._check_action(skill=skill, spec=spec, owner=owner)
            except AdminPolicyError as exc:
                status = AgentRunStatus.BLOCKED
                steps.append(AgentStep(
                    step_id="step_" + uuid4().hex,
                    index=index,
                    tool_id=spec.tool_id,
                    status=ToolCallStatus.REJECTED,
                    message=str(exc),
                    created_at=datetime.now(timezone.utc).isoformat(),
                ))
                break

            mutating = bool(spec.allowed_actions.intersection({AIActionClass.MUTATING, AIActionClass.GOVERNANCE}))
            if spec.requires_admin_approval or (mutating and owner is not AIOwnership.ADMIN):
                if owner is not AIOwnership.ADMIN and not approval_id:
                    status = AgentRunStatus.BLOCKED
                    created_approval = self.approval_queue.create(
                        task_id=str(task_id),
                        skill_id=skill_id,
                        tool_id=spec.tool_id,
                        arguments=dict(call.arguments),
                        requester=owner,
                        rationale=f"Agent step {index} cần ADMIN approval.",
                        risk_level="high" if AIActionClass.GOVERNANCE in spec.allowed_actions else "medium",
                    )
                    steps.append(AgentStep(
                        step_id="step_" + uuid4().hex,
                        index=index,
                        tool_id=spec.tool_id,
                        status=ToolCallStatus.APPROVAL_REQUIRED,
                        message="Tool chờ ADMIN phê duyệt; chưa thực thi.",
                        approval_id=created_approval.approval_id,
                        created_at=datetime.now(timezone.utc).isoformat(),
                    ))
                    break
                if not approval_id or not approval_token:
                    status = AgentRunStatus.BLOCKED
                    steps.append(AgentStep(
                        step_id="step_" + uuid4().hex,
                        index=index,
                        tool_id=spec.tool_id,
                        status=ToolCallStatus.APPROVAL_REQUIRED,
                        message="Thiếu approval_id hoặc execution token.",
                        approval_id=approval_id,
                        created_at=datetime.now(timezone.utc).isoformat(),
                    ))
                    break
                approval = self.approval_queue.authorize_execution(
                    approval_id, approval_token
                )
                if (
                    approval.task_id != str(task_id)
                    or approval.skill_id != skill_id
                    or approval.tool_id != spec.tool_id
                    or dict(approval.arguments) != dict(call.arguments)
                ):
                    raise AdminPolicyError(
                        "Approval không khớp task/skill/tool/arguments hiện tại."
                    )
                self.approval_queue.claim_execution(approval_id, approval_token)
            if mutating and owner is not AIOwnership.ADMIN and not approval_id:
                status = AgentRunStatus.BLOCKED
                steps.append(AgentStep(
                    step_id="step_" + uuid4().hex,
                    index=index,
                    tool_id=spec.tool_id,
                    status=ToolCallStatus.REJECTED,
                    message="Thao tác MUTATING/GOVERNANCE chỉ ADMIN được thực hiện.",
                    created_at=datetime.now(timezone.utc).isoformat(),
                ))
                break

            try:
                output = self.tools.handler(spec.tool_id)(dict(call.arguments))
            except Exception as exc:
                if approval_id and (spec.requires_admin_approval or mutating):
                    try:
                        self.approval_queue.mark_failed(approval_id)
                    except Exception:
                        pass  # Preserve the original handler failure.
                status = AgentRunStatus.FAILED
                steps.append(AgentStep(
                    step_id="step_" + uuid4().hex,
                    index=index,
                    tool_id=spec.tool_id,
                    status=ToolCallStatus.FAILED,
                    message=f"Tool lỗi: {exc}",
                    created_at=datetime.now(timezone.utc).isoformat(),
                ))
                break

            if approval_id and (spec.requires_admin_approval or mutating):
                try:
                    self.approval_queue.mark_executed(approval_id)
                except Exception as exc:
                    # The handler already ran; do not mark the approval FAILED.
                    # Keep EXECUTING for manual reconciliation if persistence failed.
                    status = AgentRunStatus.FAILED
                    steps.append(AgentStep(
                        step_id="step_" + uuid4().hex,
                        index=index,
                        tool_id=spec.tool_id,
                        status=ToolCallStatus.EXECUTED,
                        approval_id=approval_id,
                        message=(
                            "Tool đã thực thi nhưng không "
                            "cập nhật được trạng thái "
                            f"approval: {exc}"
                        ),
                        created_at=datetime.now(timezone.utc).isoformat(),
                    ))
                    break

            steps.append(AgentStep(
                step_id="step_" + uuid4().hex,
                index=index,
                tool_id=spec.tool_id,
                status=ToolCallStatus.EXECUTED,
                approval_id=approval_id,
                message="Tool thực thi thành công.",
                created_at=datetime.now(timezone.utc).isoformat(),
            ))

        if len(calls) > bound_limit and status is AgentRunStatus.COMPLETED:
            status = AgentRunStatus.MAX_STEPS

        completed_at = datetime.now(timezone.utc).isoformat()
        run = AgentRun(
            run_id=run_id,
            task_id=str(task_id),
            skill_id=skill_id,
            owner=owner,
            status=status,
            max_steps=bound_limit,
            steps=tuple(steps),
            created_at=now,
            completed_at=completed_at,
            audit_id=audit_id,
        )
        self.store.append(run)
        return run


def default_ai_tools() -> tuple[AIToolSpec, ...]:
    return (
        AIToolSpec(
            tool_id="classroom.status.read",
            label="Đọc trạng thái lớp",
            description="Đọc trạng thái lớp học mà không thay đổi dữ liệu.",
            allowed_actions=frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY}),
            capabilities=("classroom", "status"),
        ),
        AIToolSpec(
            tool_id="classroom.slide.open",
            label="Mở slide bài giảng",
            description="Đưa slide được chọn lên vùng trình chiếu; cần xác nhận giáo viên/ADMIN.",
            allowed_actions=frozenset({AIActionClass.MUTATING}),
            capabilities=("classroom", "slide"),
            requires_admin_approval=True,
        ),
        AIToolSpec(
            tool_id="classroom.stage.show",
            label="Hiển thị sân khấu",
            description="Hiển thị nội dung đã chọn trên sân khấu lớp học; cần xác nhận.",
            allowed_actions=frozenset({AIActionClass.MUTATING}),
            capabilities=("classroom", "stage"),
            requires_admin_approval=True,
        ),
        AIToolSpec(
            tool_id="classroom.timer.start",
            label="Bắt đầu thời gian hoạt động",
            description="Khởi động bộ đếm hoạt động; cần xác nhận.",
            allowed_actions=frozenset({AIActionClass.MUTATING}),
            capabilities=("classroom", "timer"),
            requires_admin_approval=True,
        ),
        AIToolSpec(
            tool_id="classroom.timer.stop",
            label="Dừng thời gian hoạt động",
            description="Dừng bộ đếm hoạt động; cần xác nhận.",
            allowed_actions=frozenset({AIActionClass.MUTATING}),
            capabilities=("classroom", "timer"),
            requires_admin_approval=True,
        ),
        AIToolSpec(
            tool_id="classroom.quiz.display",
            label="Hiển thị câu hỏi",
            description="Hiển thị câu hỏi đã chuẩn bị; cần xác nhận.",
            allowed_actions=frozenset({AIActionClass.MUTATING}),
            capabilities=("classroom", "quiz"),
            requires_admin_approval=True,
        ),
        AIToolSpec(
            tool_id="classroom.whiteboard.show",
            label="Hiển thị bảng",
            description="Hiển thị nội dung bảng đã chuẩn bị; cần xác nhận.",
            allowed_actions=frozenset({AIActionClass.MUTATING}),
            capabilities=("classroom", "whiteboard"),
            requires_admin_approval=True,
        ),
        AIToolSpec(
            tool_id="document.evidence.read",
            label="Đọc bằng chứng tài liệu",
            description="Đọc metadata/inventory/fingerprint đã được hệ thống tạo ra.",
            allowed_actions=frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY}),
            capabilities=("document", "reasoning"),
        ),
        AIToolSpec(
            tool_id="knowledge.approved.retrieve",
            label="Truy xuất tri thức đã duyệt",
            description="Lấy knowledge/memory APPROVED theo skill scope.",
            allowed_actions=frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY}),
            capabilities=("knowledge", "rag"),
        ),
        AIToolSpec(
            tool_id="evaluation.feedback.record",
            label="Ghi nhận phản hồi đánh giá",
            description="Ghi feedback của một Evaluation Run; không phát hành tri thức.",
            allowed_actions=frozenset({AIActionClass.ADVISORY}),
            capabilities=("evaluation",),
        ),
        AIToolSpec(
            tool_id="document.standardization.apply",
            label="Áp dụng chuẩn hóa DOCX",
            description="Thực thi transformer deterministic để thay đổi DOCX sau khi đủ điều kiện.",
            allowed_actions=frozenset({AIActionClass.MUTATING}),
            capabilities=("document", "standardization"),
            requires_admin_approval=True,
        ),
        AIToolSpec(
            tool_id="system.production.write",
            label="Thay đổi production",
            description="Tool tổng quát có side effect production; chỉ ADMIN và approval mới được phép.",
            allowed_actions=frozenset({AIActionClass.MUTATING, AIActionClass.GOVERNANCE}),
            capabilities=("system_admin",),
            admin_enabled=False,
            requires_admin_approval=True,
        ),
    )
