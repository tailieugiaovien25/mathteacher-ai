from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from ai_kernel import (
    AIOwnership,
    AIToolCall,
    AIToolRegistry,
    ApprovalQueue,
    JSONApprovalQueueStore,
    SafeAgentPlanner,
    default_ai_skills,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_admin_navigation():
    path = ROOT / "portal_v2" / "ui" / "admin_navigation.py"
    spec = importlib.util.spec_from_file_location("_admin_navigation_v10", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_ai_approval_center_is_canonical_admin_page():
    module = _load_admin_navigation()
    page = module.resolve_admin_portal_page(page_id=module.ADMIN_PAGE_AI_APPROVAL_CENTER)
    assert page.label == "AI Approval Center"

    workspace = (ROOT / "portal_v2" / "ui" / "workspace_navigation.py").read_text(encoding="utf-8")
    assert '"ai_approval_center": "Vận hành"' in workspace
    shell = (ROOT / "portal_v2" / "ui" / "admin_shell.py").read_text(encoding="utf-8")
    assert "render_admin_ai_approval_center" in shell


def test_approval_carries_plan_linkage(tmp_path: Path):
    queue = ApprovalQueue(JSONApprovalQueueStore(tmp_path / "approvals.json"))
    planner = SafeAgentPlanner(
        skills=default_ai_skills(),
        tools=AIToolRegistry(),
        approval_queue=queue,
    )
    plan = planner.plan(
        task_id="std-v10-link",
        skill_id="document.standardization.operator",
        owner=AIOwnership.SYSTEM,
        proposed_calls=[AIToolCall("document.standardization.apply", {"file": "lesson.docx"})],
    )
    approval = planner.enqueue_required_approvals(plan)[0]
    assert approval.plan_id == plan.plan_id
    assert approval.task_id == plan.task_id
    assert approval.skill_id == plan.skill_id
    assert approval.tool_id == plan.steps[0].call.tool_id
