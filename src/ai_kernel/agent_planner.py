from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from .agent_runtime import AIToolCall, AIToolRegistry
from .approval_queue import ApprovalQueue, ApprovalRequest
from .contracts import AIActionClass, AIOwnership
from .governance import AdminPolicyError
from .skills import AISkillSpec


@dataclass(frozen=True)
class PlannedStep:
    index: int
    call: AIToolCall
    action_classes: tuple[AIActionClass, ...]
    approval_required: bool
    reason: str = ""


@dataclass(frozen=True)
class AgentPlan:
    plan_id: str
    task_id: str
    skill_id: str
    owner: AIOwnership
    steps: tuple[PlannedStep, ...]
    rationale: str = ""
    created_at: str = ""

    @property
    def requires_approval(self) -> bool:
        return any(step.approval_required for step in self.steps)


class SafeAgentPlanner:
    """Deterministic planner that converts a proposed sequence into an approved-shaped plan.

    It never invents tools and never executes a tool. A future LLM planner can
    propose candidates, but this validator remains the final boundary.
    """

    def __init__(
        self,
        *,
        skills: tuple[AISkillSpec, ...],
        tools: AIToolRegistry,
        approval_queue: ApprovalQueue | None = None,
        max_steps: int = 8,
    ) -> None:
        self.skills = {item.skill_id: item for item in skills}
        self.tools = tools
        self.approval_queue = approval_queue or ApprovalQueue()
        self.max_steps = min(max(int(max_steps), 1), 32)

    def _skill(self, skill_id: str) -> AISkillSpec:
        skill = self.skills.get(skill_id)
        if skill is None or not skill.admin_enabled:
            raise AdminPolicyError(f"AI skill chưa được ADMIN bật: {skill_id}")
        return skill

    def _validate_call(self, skill: AISkillSpec, owner: AIOwnership, call: AIToolCall) -> PlannedStep:
        spec = self.tools.resolve(call.tool_id)
        actions = tuple(sorted(spec.allowed_actions, key=lambda item: item.value))
        if not set(actions).intersection(skill.allowed_actions):
            raise AdminPolicyError(f"Tool {spec.tool_id} không phù hợp skill {skill.skill_id}")
        risky = bool(set(actions).intersection({AIActionClass.MUTATING, AIActionClass.GOVERNANCE}))
        if risky and owner is not AIOwnership.ADMIN:
            approval_required = True
            reason = "Thao tác có side effect; cần ADMIN phê duyệt trước khi thực thi."
        else:
            approval_required = bool(spec.requires_admin_approval)
            reason = "Tool có cấu hình yêu cầu approval của ADMIN." if approval_required else ""
        return PlannedStep(
            index=0,
            call=call,
            action_classes=actions,
            approval_required=approval_required,
            reason=reason,
        )

    def plan(
        self,
        *,
        task_id: str,
        skill_id: str,
        owner: AIOwnership,
        proposed_calls: list[AIToolCall] | tuple[AIToolCall, ...],
        rationale: str = "",
    ) -> AgentPlan:
        skill = self._skill(skill_id)
        calls = tuple(proposed_calls)
        if not calls:
            raise ValueError("Agent plan không được rỗng.")
        if len(calls) > self.max_steps:
            raise AdminPolicyError(f"Plan vượt max_steps={self.max_steps}.")
        validated = tuple(self._validate_call(skill, owner, call) for call in calls)
        steps = tuple(
            PlannedStep(
                index=i,
                call=validated_step.call,
                action_classes=validated_step.action_classes,
                approval_required=validated_step.approval_required,
                reason=validated_step.reason,
            )
            for i, validated_step in enumerate(validated, start=1)
        )
        return AgentPlan(
            plan_id="plan_" + uuid4().hex,
            task_id=str(task_id),
            skill_id=skill.skill_id,
            owner=owner,
            steps=steps,
            rationale=str(rationale),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def enqueue_required_approvals(self, plan: AgentPlan) -> tuple[ApprovalRequest, ...]:
        requests: list[ApprovalRequest] = []
        for step in plan.steps:
            if not step.approval_required:
                continue
            requests.append(self.approval_queue.create(
                task_id=plan.task_id,
                skill_id=plan.skill_id,
                plan_id=plan.plan_id,
                tool_id=step.call.tool_id,
                arguments=dict(step.call.arguments),
                requester=plan.owner,
                rationale=step.reason or plan.rationale,
                risk_level="high" if AIActionClass.GOVERNANCE in step.action_classes else "medium",
            ))
        return tuple(requests)
