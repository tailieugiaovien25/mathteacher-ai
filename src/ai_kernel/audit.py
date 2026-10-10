from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from .contracts import AIKernelRequest


@dataclass(frozen=True)
class AIKernelAuditEvent:
    audit_id: str
    created_at: str
    task_id: str
    owner: str
    action: str
    profile_id: str
    skill_id: str = ""


def make_audit_event(request: AIKernelRequest, profile_id: str) -> AIKernelAuditEvent:
    return AIKernelAuditEvent(
        audit_id="aik_" + uuid4().hex,
        created_at=datetime.now(timezone.utc).isoformat(),
        task_id=request.task_id,
        owner=request.owner.value,
        action=request.action.value,
        profile_id=profile_id,
        skill_id=request.skill_id,
    )
