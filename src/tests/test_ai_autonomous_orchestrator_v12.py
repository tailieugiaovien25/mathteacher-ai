from __future__ import annotations

from pathlib import Path

from ai_kernel import (
    AIOwnership,
    AIToolCall,
    AIToolRegistry,
    ApprovalQueue,
    JSONAgentRunStore,
    JSONApprovalQueueStore,
    JSONAutonomousRunStore,
    SafeAgentPlanner,
    SafeAgentRuntime,
    AutonomousOrchestrator,
    AutonomousRunStatus,
    default_ai_skills,
)


def _make(tmp_path: Path):
    queue = ApprovalQueue(JSONApprovalQueueStore(tmp_path / "approvals.json"))
    tools = AIToolRegistry()
    tools.bind("document.evidence.read", lambda args: {"ok": True, "args": dict(args)})
    tools.bind("document.standardization.apply", lambda args: {"changed": True, "args": dict(args)})
    planner = SafeAgentPlanner(
        skills=default_ai_skills(),
        tools=tools,
        approval_queue=queue,
        max_steps=3,
    )
    runtime = SafeAgentRuntime(
        skills=default_ai_skills(),
        tools=tools,
        store=JSONAgentRunStore(tmp_path / "agent_runs.json"),
        approval_queue=queue,
        default_max_steps=3,
    )
    orchestrator = AutonomousOrchestrator(
        planner=planner,
        runtime=runtime,
        approval_queue=queue,
        store=JSONAutonomousRunStore(tmp_path / "autonomous_runs.json"),
        max_cycles=3,
    )
    return orchestrator, queue


def test_autonomous_orchestrator_completes_when_planner_stops(tmp_path: Path):
    orchestrator, _ = _make(tmp_path)
    calls = iter([
        (AIToolCall("document.evidence.read", {"page": 1}),),
        (),
    ])
    run = orchestrator.run(
        task_id="auto-v12-read",
        skill_id="document.standardization.audit",
        owner=AIOwnership.SYSTEM,
        objective="Kiểm tra bằng chứng giáo án",
        planner_provider=lambda _ctx: next(calls),
    )
    assert run.status is AutonomousRunStatus.COMPLETED
    assert run.cycle_count == 2
    assert len(run.agent_run_ids) == 1


def test_autonomous_orchestrator_stops_for_mutating_approval(tmp_path: Path):
    orchestrator, queue = _make(tmp_path)
    run = orchestrator.run(
        task_id="auto-v12-mutate",
        skill_id="document.standardization.operator",
        owner=AIOwnership.SYSTEM,
        objective="Chuẩn hóa DOCX sau khi kiểm định",
        planner_provider=lambda _ctx: (
            AIToolCall("document.standardization.apply", {"file": "lesson.docx"}),
        ),
    )
    assert run.status is AutonomousRunStatus.WAITING_APPROVAL
    assert len(run.approval_ids) == 1
    assert queue.get(run.approval_ids[0]).status.value == "pending"


def test_autonomous_orchestrator_is_bounded(tmp_path: Path):
    orchestrator, _ = _make(tmp_path)
    run = orchestrator.run(
        task_id="auto-v12-bound",
        skill_id="document.standardization.audit",
        owner=AIOwnership.SYSTEM,
        objective="Không dừng kế hoạch",
        planner_provider=lambda _ctx: (AIToolCall("document.evidence.read"),),
        max_cycles=2,
    )
    assert run.status is AutonomousRunStatus.MAX_CYCLES
    assert run.cycle_count == 2


def test_admin_control_center_route_registered():
    nav_path = Path(__file__).resolve().parents[1] / "portal_v2" / "ui" / "admin_navigation.py"
    text = nav_path.read_text(encoding="utf-8")
    assert 'ADMIN_PAGE_AI_AUTONOMOUS_CENTER = "ai_autonomous_center"' in text
    assert 'AdminPortalPage(ADMIN_PAGE_AI_AUTONOMOUS_CENTER, "AI Autonomous Control Center")' in text

    route_path = Path(__file__).resolve().parents[1] / "portal_v2" / "ui" / "workspace_navigation.py"
    route_text = route_path.read_text(encoding="utf-8")
    assert '"ai_autonomous_center": "Vận hành"' in route_text
