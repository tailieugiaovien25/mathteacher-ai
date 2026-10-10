from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

from .agent_planner import AgentPlan, SafeAgentPlanner
from .agent_runtime import AIToolCall, AgentRun, AgentRunStatus, SafeAgentRuntime
from .approval_queue import ApprovalQueue, ApprovalRequest
from .contracts import AIOwnership
from .governance import AdminPolicyError


class AutonomousRunStatus(str, Enum):
    COMPLETED = "completed"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    FAILED = "failed"
    MAX_CYCLES = "max_cycles"


@dataclass(frozen=True)
class AutonomousContext:
    """Bounded context passed to the next planning cycle.

    The context intentionally carries identifiers and summaries, not arbitrary
    Python objects. This makes the supervisor auditable and keeps the Kernel
    independent from model/runtime implementation details.
    """

    run_id: str
    task_id: str
    objective: str
    skill_id: str
    cycle: int
    completed_tool_ids: tuple[str, ...] = ()
    approval_ids: tuple[str, ...] = ()
    last_status: str = ""
    observation: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AutonomousRun:
    run_id: str
    task_id: str
    skill_id: str
    owner: AIOwnership
    objective: str
    status: AutonomousRunStatus
    max_cycles: int
    cycle_count: int
    plan_ids: tuple[str, ...] = ()
    approval_ids: tuple[str, ...] = ()
    agent_run_ids: tuple[str, ...] = ()
    stop_reason: str = ""
    audit_id: str = ""
    created_at: str = ""
    completed_at: str = ""


class JSONAutonomousRunStore:
    """Local-first store for autonomous supervisor runs."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = Path(path or os.getenv("MATH_TEACHER_AI_AUTONOMOUS_RUNS", ".mathteacher_ai/autonomous_runs.json"))
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
        fd, temp_name = tempfile.mkstemp(prefix="autonomous-runs-", suffix=".json", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(rows, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def append(self, run: AutonomousRun) -> None:
        rows = self._read()
        rows.append(asdict(run) | {"owner": run.owner.value, "status": run.status.value})
        self._write(rows)

    def all(self) -> tuple[AutonomousRun, ...]:
        rows = self._read()
        result: list[AutonomousRun] = []
        for row in rows:
            try:
                result.append(
                    AutonomousRun(
                        **{
                            **row,
                            "owner": AIOwnership(row.get("owner", AIOwnership.SYSTEM.value)),
                            "status": AutonomousRunStatus(row.get("status", AutonomousRunStatus.FAILED.value)),
                            "plan_ids": tuple(row.get("plan_ids", ()) or ()),
                            "approval_ids": tuple(row.get("approval_ids", ()) or ()),
                            "agent_run_ids": tuple(row.get("agent_run_ids", ()) or ()),
                        }
                    )
                )
            except (TypeError, ValueError):
                continue
        return tuple(result)

    def get(self, run_id: str) -> AutonomousRun:
        for run in self.all():
            if run.run_id == run_id:
                return run
        raise AdminPolicyError(f"Không tìm thấy autonomous run: {run_id}")


PlannerProvider = Callable[[AutonomousContext], Sequence[AIToolCall]]
ObservationProvider = Callable[[AgentRun, AutonomousContext], Mapping[str, Any]]


class AutonomousOrchestrator:
    """Bounded supervisor for self-running AI workflows.

    A model-backed planner may propose tool calls through ``planner_provider``;
    SafeAgentPlanner remains the deterministic boundary that validates every
    call. Read-only/advisory steps may execute automatically. Any mutating or
    governance step is converted into an ADMIN approval request and the
    supervisor stops with WAITING_APPROVAL.

    The orchestrator cannot modify the Kernel, tool registry, runtime model
    configuration, or governance policy. Its "autonomy" is bounded by max
    cycles, registered skills/tools, and the existing Approval Queue.
    """

    def __init__(
        self,
        *,
        planner: SafeAgentPlanner,
        runtime: SafeAgentRuntime,
        approval_queue: ApprovalQueue,
        store: JSONAutonomousRunStore | None = None,
        max_cycles: int = 6,
        observation_provider: ObservationProvider | None = None,
    ) -> None:
        if max_cycles < 1:
            raise ValueError("max_cycles must be >= 1")
        self.planner = planner
        self.runtime = runtime
        self.approval_queue = approval_queue
        self.store = store or JSONAutonomousRunStore()
        self.max_cycles = min(int(max_cycles), 16)
        self.observation_provider = observation_provider or (lambda _run, _ctx: {})

    def run(
        self,
        *,
        task_id: str,
        skill_id: str,
        owner: AIOwnership,
        objective: str,
        planner_provider: PlannerProvider,
        max_cycles: int | None = None,
    ) -> AutonomousRun:
        if not str(task_id).strip() or not str(objective).strip():
            raise ValueError("task_id và objective không được để trống")
        cycles = self.max_cycles if max_cycles is None else min(max(int(max_cycles), 1), 16)
        run_id = "auto_" + uuid4().hex
        audit_id = "autoa_" + uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat()
        context = AutonomousContext(
            run_id=run_id,
            task_id=str(task_id),
            objective=str(objective).strip(),
            skill_id=str(skill_id),
            cycle=0,
        )
        plan_ids: list[str] = []
        approval_ids: list[str] = []
        agent_run_ids: list[str] = []
        completed_tools: list[str] = []
        observation: Mapping[str, Any] = {}
        stop_reason = ""
        final_status = AutonomousRunStatus.MAX_CYCLES
        cycle_count = 0

        for cycle in range(1, cycles + 1):
            cycle_count = cycle
            context = AutonomousContext(
                run_id=run_id,
                task_id=context.task_id,
                objective=context.objective,
                skill_id=context.skill_id,
                cycle=cycle,
                completed_tool_ids=tuple(completed_tools),
                approval_ids=tuple(approval_ids),
                last_status=context.last_status,
                observation=observation,
            )
            calls = tuple(planner_provider(context))
            if not calls:
                final_status = AutonomousRunStatus.COMPLETED
                stop_reason = "Planner không còn bước cần thực hiện."
                break

            plan = self.planner.plan(
                task_id=context.task_id,
                skill_id=context.skill_id,
                owner=owner,
                proposed_calls=calls,
                rationale=context.objective,
            )
            plan_ids.append(plan.plan_id)
            requests = self.planner.enqueue_required_approvals(plan)
            if requests:
                approval_ids.extend(item.approval_id for item in requests)
                final_status = AutonomousRunStatus.WAITING_APPROVAL
                stop_reason = "Có bước MUTATING/GOVERNANCE cần ADMIN phê duyệt; supervisor đã dừng trước side effect."
                break

            agent_run = self.runtime.run(
                task_id=context.task_id,
                skill_id=context.skill_id,
                owner=owner,
                plan=tuple(step.call for step in plan.steps),
            )
            agent_run_ids.append(agent_run.run_id)
            if agent_run.status is AgentRunStatus.COMPLETED:
                for step in agent_run.steps:
                    if step.tool_id:
                        completed_tools.append(step.tool_id)
                observation = dict(self.observation_provider(agent_run, context) or {})
                context = AutonomousContext(
                    run_id=run_id,
                    task_id=context.task_id,
                    objective=context.objective,
                    skill_id=context.skill_id,
                    cycle=cycle,
                    completed_tool_ids=tuple(completed_tools),
                    approval_ids=tuple(approval_ids),
                    last_status=agent_run.status.value,
                    observation=observation,
                )
                # A planner that wants another cycle can return more calls; an
                # empty proposal on the next cycle signals completion.
                final_status = AutonomousRunStatus.COMPLETED
                stop_reason = "Cycle đã hoàn thành; chờ planner xác định có cần bước tiếp theo hay không."
                continue
            if agent_run.status is AgentRunStatus.MAX_STEPS:
                final_status = AutonomousRunStatus.MAX_CYCLES
                stop_reason = "Agent runtime chạm giới hạn bước trong một cycle."
                break
            if agent_run.status is AgentRunStatus.BLOCKED:
                final_status = AutonomousRunStatus.BLOCKED
                stop_reason = "Agent runtime bị governance chặn."
                break
            final_status = AutonomousRunStatus.FAILED
            stop_reason = "Agent runtime thất bại trong cycle."
            break
        else:
            final_status = AutonomousRunStatus.MAX_CYCLES
            stop_reason = f"Đã đạt max_cycles={cycles}."

        completed_at = datetime.now(timezone.utc).isoformat()
        run = AutonomousRun(
            run_id=run_id,
            task_id=str(task_id),
            skill_id=str(skill_id),
            owner=owner,
            objective=str(objective).strip(),
            status=final_status,
            max_cycles=cycles,
            cycle_count=cycle_count,
            plan_ids=tuple(plan_ids),
            approval_ids=tuple(approval_ids),
            agent_run_ids=tuple(agent_run_ids),
            stop_reason=stop_reason,
            audit_id=audit_id,
            created_at=created_at,
            completed_at=completed_at,
        )
        self.store.append(run)
        return run
