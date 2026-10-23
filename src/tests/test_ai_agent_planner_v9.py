from __future__ import annotations

from pathlib import Path
import multiprocessing

import pytest

from ai_kernel import (
    AIOwnership,
    AIActionClass,
    AIToolCall,
    AIToolRegistry,
    AgentPlan,
    ApprovalQueue,
    ApprovalStatus,
    AISkillDomain,
    AISkillSpec,
    JSONApprovalQueueStore,
    PlannedStep,
    SafeAgentPlanner,
    default_ai_skills,
)
from ai_kernel.governance import AdminPolicyError


def _queue(tmp_path: Path) -> ApprovalQueue:
    return ApprovalQueue(JSONApprovalQueueStore(tmp_path / "approvals.json"))


def _approval_race_worker(path, approval_id, action, barrier, results):
    try:
        queue = ApprovalQueue(JSONApprovalQueueStore(path))
        barrier.wait(timeout=15)
        if action == "approve":
            result = queue.approve(
                approval_id,
                admin_actor="admin-race",
                actor_owner=AIOwnership.ADMIN,
            )
        elif action == "reject":
            result = queue.reject(
                approval_id,
                admin_actor="admin-race",
                actor_owner=AIOwnership.ADMIN,
                reason="race test",
            )
        elif action == "claim":
            request = queue.get(approval_id)
            result = queue.claim_execution(
                approval_id, request.execution_token
            )
        else:
            raise ValueError(f"Unknown action: {action}")
        results.put(("ok", result.status.value))
    except AdminPolicyError:
        results.put(("denied", "AdminPolicyError"))
    except BaseException as exc:
        results.put(("error", repr(exc)))


def _run_process_race(path, approval_id, actions):
    ctx = multiprocessing.get_context("spawn")
    barrier = ctx.Barrier(len(actions))
    results = ctx.Queue()
    processes = [
        ctx.Process(
            target=_approval_race_worker,
            args=(str(path), approval_id, action, barrier, results),
        )
        for action in actions
    ]
    try:
        for process in processes:
            process.start()
        for process in processes:
            process.join(timeout=25)

        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)

        assert all(not process.is_alive() for process in processes)
        assert all(process.exitcode == 0 for process in processes)

        outcomes = [results.get(timeout=5) for _ in processes]
        assert all(kind != "error" for kind, _ in outcomes), outcomes
        return outcomes
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
        results.close()
        results.join_thread()


def test_concurrent_admin_decisions_are_atomic(tmp_path: Path):
    queue = _queue(tmp_path)
    request = queue.create(
        task_id="race-decision",
        skill_id="s",
        tool_id="t",
        requester=AIOwnership.SYSTEM,
    )

    outcomes = _run_process_race(
        tmp_path / "approvals.json",
        request.approval_id,
        ["approve", "reject"],
    )

    assert sorted(kind for kind, _ in outcomes) == ["denied", "ok"]
    final_request = queue.get(request.approval_id)
    assert final_request.status in {
        ApprovalStatus.APPROVED,
        ApprovalStatus.REJECTED,
    }


def test_concurrent_processes_can_claim_execution_token_only_once(tmp_path: Path):
    queue = _queue(tmp_path)
    request = queue.create(
        task_id="race-claim",
        skill_id="s",
        tool_id="t",
        requester=AIOwnership.SYSTEM,
    )
    approved = queue.approve(
        request.approval_id,
        admin_actor="admin-race",
        actor_owner=AIOwnership.ADMIN,
    )

    outcomes = _run_process_race(
        tmp_path / "approvals.json",
        approved.approval_id,
        ["claim", "claim"],
    )

    assert sorted(kind for kind, _ in outcomes) == ["denied", "ok"]
    assert queue.get(approved.approval_id).status is ApprovalStatus.EXECUTING


def _planner(tmp_path: Path) -> tuple[SafeAgentPlanner, ApprovalQueue]:
    queue = _queue(tmp_path)
    tools = AIToolRegistry()
    skills = default_ai_skills()
    return SafeAgentPlanner(skills=skills, tools=tools, approval_queue=queue, max_steps=3), queue


def test_plan_accepts_registered_read_only_tool(tmp_path: Path):
    planner, _ = _planner(tmp_path)
    plan = planner.plan(
        task_id="std-v9-1",
        skill_id="document.standardization.audit",
        owner=AIOwnership.SYSTEM,
        proposed_calls=[AIToolCall("document.evidence.read", {"page": 1})],
    )
    assert isinstance(plan, AgentPlan)
    assert plan.steps[0].index == 1
    assert plan.steps[0].approval_required is False


def test_plan_rejects_unknown_tool(tmp_path: Path):
    planner, _ = _planner(tmp_path)
    with pytest.raises(AdminPolicyError):
        planner.plan(
            task_id="std-v9-2",
            skill_id="document.standardization.audit",
            owner=AIOwnership.SYSTEM,
            proposed_calls=[AIToolCall("unknown.tool")],
        )


def test_plan_rejects_skill_tool_mismatch(tmp_path: Path):
    planner, _ = _planner(tmp_path)
    with pytest.raises(AdminPolicyError):
        planner.plan(
            task_id="std-v9-3",
            skill_id="document.standardization.audit",
            owner=AIOwnership.SYSTEM,
            proposed_calls=[AIToolCall("document.standardization.apply", {"file": "a.docx"})],
        )


def test_mutating_plan_is_approval_required(tmp_path: Path):
    planner, _ = _planner(tmp_path)
    plan = planner.plan(
        task_id="std-v9-4",
        skill_id="document.standardization.operator",
        owner=AIOwnership.SYSTEM,
        proposed_calls=[AIToolCall("document.standardization.apply", {"file": "a.docx"})],
    )
    assert plan.requires_approval is True
    assert plan.steps[0].approval_required is True


def test_approval_request_is_enqueued(tmp_path: Path):
    planner, queue = _planner(tmp_path)
    plan = planner.plan(
        task_id="std-v9-5",
        skill_id="document.standardization.operator",
        owner=AIOwnership.SYSTEM,
        proposed_calls=[AIToolCall("document.standardization.apply", {"file": "a.docx"})],
    )
    requests = planner.enqueue_required_approvals(plan)
    assert len(requests) == 1
    assert requests[0].status is ApprovalStatus.PENDING
    assert queue.pending()[0].approval_id == requests[0].approval_id


def test_only_admin_can_approve(tmp_path: Path):
    queue = _queue(tmp_path)
    request = queue.create(task_id="x", skill_id="s", tool_id="t", requester=AIOwnership.SYSTEM)
    with pytest.raises(AdminPolicyError):
        queue.approve(request.approval_id, admin_actor="", actor_owner=AIOwnership.USER)
    approved = queue.approve(request.approval_id, admin_actor="admin-1", actor_owner=AIOwnership.ADMIN)
    assert approved.status is ApprovalStatus.APPROVED
    assert approved.execution_token


def test_rejected_approval_cannot_authorize_execution(tmp_path: Path):
    queue = _queue(tmp_path)
    request = queue.create(task_id="x", skill_id="s", tool_id="t", requester=AIOwnership.USER)
    queue.reject(request.approval_id, admin_actor="admin-1", actor_owner=AIOwnership.ADMIN, reason="Không phù hợp")
    with pytest.raises(AdminPolicyError):
        queue.authorize_execution(request.approval_id, "anything")


def test_wrong_execution_token_is_rejected(tmp_path: Path):
    queue = _queue(tmp_path)
    request = queue.create(task_id="x", skill_id="s", tool_id="t", requester=AIOwnership.SYSTEM)
    approved = queue.approve(request.approval_id, admin_actor="admin-1", actor_owner=AIOwnership.ADMIN)
    with pytest.raises(AdminPolicyError):
        queue.authorize_execution(approved.approval_id, "bad")


def test_approved_request_can_be_authorized_and_marked_executed(
    tmp_path: Path,
):
    queue = _queue(tmp_path)
    request = queue.create(
        task_id="x",
        skill_id="s",
        tool_id="t",
        requester=AIOwnership.ADMIN,
    )
    approved = queue.approve(
        request.approval_id,
        admin_actor="admin-1",
        actor_owner=AIOwnership.ADMIN,
    )
    authorized = queue.authorize_execution(
        approved.approval_id, approved.execution_token
    )
    assert authorized.status is ApprovalStatus.APPROVED

    claimed = queue.claim_execution(
        approved.approval_id, approved.execution_token
    )
    assert claimed.status is ApprovalStatus.EXECUTING

    executed = queue.mark_executed(approved.approval_id)
    assert executed.status is ApprovalStatus.EXECUTED



def test_approval_execution_token_can_only_be_claimed_once(
    tmp_path: Path,
):
    queue = _queue(tmp_path)
    request = queue.create(
        task_id="x", skill_id="s", tool_id="t",
        requester=AIOwnership.ADMIN,
    )
    approved = queue.approve(
        request.approval_id,
        admin_actor="admin-1",
        actor_owner=AIOwnership.ADMIN,
    )

    claimed = queue.claim_execution(
        approved.approval_id, approved.execution_token
    )
    assert claimed.status is ApprovalStatus.EXECUTING

    with pytest.raises(AdminPolicyError):
        queue.claim_execution(approved.approval_id, approved.execution_token)


def test_failed_approval_cannot_be_reused(tmp_path: Path):
    queue = _queue(tmp_path)
    request = queue.create(
        task_id="x", skill_id="s", tool_id="t",
        requester=AIOwnership.ADMIN,
    )
    approved = queue.approve(
        request.approval_id,
        admin_actor="admin-1",
        actor_owner=AIOwnership.ADMIN,
    )
    queue.claim_execution(approved.approval_id, approved.execution_token)
    failed = queue.mark_failed(approved.approval_id)
    assert failed.status is ApprovalStatus.FAILED

    with pytest.raises(AdminPolicyError):
        queue.claim_execution(approved.approval_id, approved.execution_token)


def test_planner_is_bounded(tmp_path: Path):
    planner, _ = _planner(tmp_path)
    with pytest.raises(AdminPolicyError):
        planner.plan(
            task_id="bounded",
            skill_id="document.standardization.audit",
            owner=AIOwnership.SYSTEM,
            proposed_calls=[
                AIToolCall("document.evidence.read"),
                AIToolCall("document.evidence.read"),
                AIToolCall("document.evidence.read"),
                AIToolCall("document.evidence.read"),
            ],
        )


def test_runtime_creates_pending_approval_for_mutating_call(tmp_path: Path):
    from ai_kernel import JSONAgentRunStore, SafeAgentRuntime, AgentRunStatus, ToolCallStatus
    queue = _queue(tmp_path)
    tools = AIToolRegistry()
    observed = []
    tools.bind("document.standardization.apply", lambda args: observed.append(args) or {"changed": True})
    runtime = SafeAgentRuntime(
        skills=default_ai_skills(),
        tools=tools,
        store=JSONAgentRunStore(tmp_path / "agent-runs.json"),
        approval_queue=queue,
    )
    run = runtime.run(
        task_id="std-v9-runtime-1",
        skill_id="document.standardization.operator",
        owner=AIOwnership.SYSTEM,
        plan=[AIToolCall("document.standardization.apply", {"file": "a.docx"})],
    )
    assert run.status is AgentRunStatus.BLOCKED
    assert run.steps[0].status is ToolCallStatus.APPROVAL_REQUIRED
    assert observed == []
    assert queue.pending()


def test_runtime_executes_only_matching_approved_request(tmp_path: Path):
    from ai_kernel import JSONAgentRunStore, SafeAgentRuntime, AgentRunStatus, ToolCallStatus
    queue = _queue(tmp_path)
    tools = AIToolRegistry()
    observed = []
    tools.bind("document.standardization.apply", lambda args: observed.append(args) or {"changed": True})
    runtime = SafeAgentRuntime(
        skills=default_ai_skills(),
        tools=tools,
        store=JSONAgentRunStore(tmp_path / "agent-runs.json"),
        approval_queue=queue,
    )
    request = queue.create(
        task_id="std-v9-runtime-2",
        skill_id="document.standardization.operator",
        tool_id="document.standardization.apply",
        arguments={"file": "a.docx"},
        requester=AIOwnership.SYSTEM,
    )
    approved = queue.approve(request.approval_id, admin_actor="admin-1", actor_owner=AIOwnership.ADMIN)
    run = runtime.run(
        task_id=request.task_id,
        skill_id=request.skill_id,
        owner=AIOwnership.SYSTEM,
        plan=[AIToolCall(request.tool_id, request.arguments)],
        approval_id=approved.approval_id,
        approval_token=approved.execution_token,
    )
    assert run.status is AgentRunStatus.COMPLETED
    assert run.steps[0].status is ToolCallStatus.EXECUTED
    assert observed == [{"file": "a.docx"}]
    assert queue.get(request.approval_id).status is ApprovalStatus.EXECUTED


def test_runtime_marks_approval_failed_when_handler_raises(tmp_path: Path):
    from ai_kernel import JSONAgentRunStore, SafeAgentRuntime, AgentRunStatus, ToolCallStatus

    queue = _queue(tmp_path)
    tools = AIToolRegistry()
    calls = []

    def failing_handler(args):
        calls.append(dict(args))
        raise RuntimeError("simulated handler failure")

    tools.bind("document.standardization.apply", failing_handler)
    runtime = SafeAgentRuntime(
        skills=default_ai_skills(),
        tools=tools,
        store=JSONAgentRunStore(tmp_path / "agent-runs.json"),
        approval_queue=queue,
    )

    request = queue.create(
        task_id="std-v9-runtime-failure",
        skill_id="document.standardization.operator",
        tool_id="document.standardization.apply",
        arguments={"file": "a.docx"},
        requester=AIOwnership.SYSTEM,
    )
    approved = queue.approve(
        request.approval_id,
        admin_actor="admin-1",
        actor_owner=AIOwnership.ADMIN,
    )

    run = runtime.run(
        task_id=request.task_id,
        skill_id=request.skill_id,
        owner=AIOwnership.SYSTEM,
        plan=[AIToolCall(request.tool_id, request.arguments)],
        approval_id=approved.approval_id,
        approval_token=approved.execution_token,
    )

    assert run.status is AgentRunStatus.FAILED
    assert run.steps[0].status is ToolCallStatus.FAILED
    assert calls == [{"file": "a.docx"}]
    assert queue.get(request.approval_id).status is ApprovalStatus.FAILED

    # Token c? kh?ng ???c d?ng ?? th?c thi l?i approval ?? th?t b?i.
    with pytest.raises(AdminPolicyError):
        runtime.run(
            task_id=request.task_id,
            skill_id=request.skill_id,
            owner=AIOwnership.SYSTEM,
            plan=[AIToolCall(request.tool_id, request.arguments)],
            approval_id=approved.approval_id,
            approval_token=approved.execution_token,
        )

    assert calls == [{"file": "a.docx"}]


def test_runtime_rejects_approval_for_different_arguments(tmp_path: Path):
    from ai_kernel import JSONAgentRunStore, SafeAgentRuntime
    queue = _queue(tmp_path)
    tools = AIToolRegistry()
    tools.bind("document.standardization.apply", lambda args: {"changed": True})
    runtime = SafeAgentRuntime(
        skills=default_ai_skills(),
        tools=tools,
        store=JSONAgentRunStore(tmp_path / "agent-runs.json"),
        approval_queue=queue,
    )
    request = queue.create(
        task_id="std-v9-runtime-3",
        skill_id="document.standardization.operator",
        tool_id="document.standardization.apply",
        arguments={"file": "a.docx"},
        requester=AIOwnership.SYSTEM,
    )
    approved = queue.approve(request.approval_id, admin_actor="admin-1", actor_owner=AIOwnership.ADMIN)
    with pytest.raises(AdminPolicyError):
        runtime.run(
            task_id=request.task_id,
            skill_id=request.skill_id,
            owner=AIOwnership.SYSTEM,
            plan=[AIToolCall(request.tool_id, {"file": "other.docx"})],
            approval_id=approved.approval_id,
            approval_token=approved.execution_token,
        )
