from __future__ import annotations

from pathlib import Path

import pytest

from ai_kernel import (
    AIActionClass,
    AIOwnership,
    AIToolCall,
    AIToolRegistry,
    AIToolSpec,
    AgentRunStatus,
    JSONAgentRunStore,
    SafeAgentRuntime,
    ToolCallStatus,
    default_ai_skills,
    AISkillSpec,
    AISkillDomain,
)
from ai_kernel.governance import AdminPolicyError


def _runtime(tmp_path: Path, *, tools=None) -> SafeAgentRuntime:
    return SafeAgentRuntime(
        skills=default_ai_skills(),
        tools=tools,
        store=JSONAgentRunStore(tmp_path / "agent_runs.json"),
        default_max_steps=3,
    )


def test_read_only_tool_runs_and_is_audited(tmp_path: Path):
    tools = AIToolRegistry()
    observed = []
    tools.bind("document.evidence.read", lambda args: observed.append(args) or {"ok": True})
    runtime = _runtime(tmp_path, tools=tools)
    run = runtime.run(
        task_id="std-001",
        skill_id="document.standardization.audit",
        owner=AIOwnership.SYSTEM,
        plan=[AIToolCall("document.evidence.read", {"page": 4})],
    )
    assert run.status is AgentRunStatus.COMPLETED
    assert run.steps[0].status is ToolCallStatus.EXECUTED
    assert observed == [{"page": 4}]


def test_unknown_tool_is_blocked(tmp_path: Path):
    runtime = _runtime(tmp_path)
    with pytest.raises(AdminPolicyError):
        runtime.run(
            task_id="x",
            skill_id="document.standardization.audit",
            owner=AIOwnership.SYSTEM,
            plan=[AIToolCall("unknown.tool")],
        )


def test_disabled_tool_is_not_executable(tmp_path: Path):
    tools = AIToolRegistry((AIToolSpec(
        "disabled.tool", "Disabled", "test",
        frozenset({AIActionClass.READ_ONLY}), admin_enabled=False,
    ),))
    with pytest.raises(AdminPolicyError):
        tools.resolve("disabled.tool")


def test_mutating_standardizer_requires_approval_and_does_not_run(tmp_path: Path):
    tools = AIToolRegistry()
    called = []
    tools.bind("document.standardization.apply", lambda args: called.append(args) or {"changed": True})
    approval_skill = AISkillSpec(
        "document.standardization.operator",
        "Chuẩn hóa DOCX có kiểm soát",
        AISkillDomain.DOCUMENT,
        ("document", "standardization"),
        frozenset({AIActionClass.READ_ONLY, AIActionClass.ADVISORY, AIActionClass.MUTATING}),
        admin_enabled=True,
    )
    runtime = SafeAgentRuntime(
        skills=(*default_ai_skills(), approval_skill),
        tools=tools,
        store=JSONAgentRunStore(tmp_path / "agent_runs.json"),
        default_max_steps=3,
    )
    run = runtime.run(
        task_id="std-002",
        skill_id="document.standardization.operator",
        owner=AIOwnership.USER,
        plan=[AIToolCall("document.standardization.apply", {"file": "lesson.docx"})],
    )
    assert run.status is AgentRunStatus.BLOCKED
    assert run.steps[0].status is ToolCallStatus.APPROVAL_REQUIRED
    assert called == []


def test_max_steps_bounds_autonomous_loop(tmp_path: Path):
    tools = AIToolRegistry()
    tools.bind("document.evidence.read", lambda args: {"ok": True})
    runtime = _runtime(tmp_path, tools=tools)
    run = runtime.run(
        task_id="bounded",
        skill_id="document.standardization.audit",
        owner=AIOwnership.SYSTEM,
        max_steps=2,
        plan=[AIToolCall("document.evidence.read"), AIToolCall("document.evidence.read"), AIToolCall("document.evidence.read")],
    )
    assert run.status is AgentRunStatus.MAX_STEPS
    assert len(run.steps) == 2


def test_agent_cannot_escalate_by_using_tool_action_not_allowed_by_skill(tmp_path: Path):
    tools = AIToolRegistry((AIToolSpec(
        "governance.probe", "Governance probe", "test",
        frozenset({AIActionClass.GOVERNANCE}), admin_enabled=True,
    ),))
    runtime = _runtime(tmp_path, tools=tools)
    run = runtime.run(
        task_id="escalate",
        skill_id="document.standardization.audit",
        owner=AIOwnership.ADMIN,
        plan=[AIToolCall("governance.probe")],
    )
    assert run.status is AgentRunStatus.BLOCKED
    assert run.steps[0].status is ToolCallStatus.REJECTED
