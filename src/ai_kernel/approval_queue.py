from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from .contracts import AIOwnership
from .governance import AdminPolicyError


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"


@dataclass(frozen=True)
class ApprovalRequest:
    approval_id: str
    task_id: str
    skill_id: str
    tool_id: str
    arguments: dict[str, Any]
    requester: AIOwnership
    plan_id: str = ""
    rationale: str = ""
    risk_level: str = "medium"
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = ""
    decided_at: str = ""
    decided_by: str = ""
    execution_token: str = ""
    rejection_reason: str = ""


class JSONApprovalQueueStore:
    """Local-first persistent store for ADMIN approval requests."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = Path(path or os.getenv("MATH_TEACHER_AI_APPROVALS", ".mathteacher_ai/approval_queue.json"))
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
        fd, temp_name = tempfile.mkstemp(prefix="approval-", suffix=".json", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(rows, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def all(self) -> tuple[ApprovalRequest, ...]:
        rows = self._read()
        result: list[ApprovalRequest] = []
        for row in rows:
            try:
                result.append(ApprovalRequest(
                    **{**row, "status": ApprovalStatus(row.get("status", ApprovalStatus.PENDING.value)),
                       "requester": AIOwnership(row.get("requester", AIOwnership.SYSTEM.value))}
                ))
            except (TypeError, ValueError):
                continue
        return tuple(result)

    def upsert(self, request: ApprovalRequest) -> None:
        rows = self._read()
        payload = asdict(request) | {"status": request.status.value, "requester": request.requester.value}
        replaced = False
        for idx, row in enumerate(rows):
            if row.get("approval_id") == request.approval_id:
                rows[idx] = payload
                replaced = True
                break
        if not replaced:
            rows.append(payload)
        self._write(rows)


class ApprovalQueue:
    """ADMIN-owned approval queue; the queue itself cannot execute tools."""

    def __init__(self, store: JSONApprovalQueueStore | None = None) -> None:
        self.store = store or JSONApprovalQueueStore()

    def create(
        self,
        *,
        task_id: str,
        skill_id: str,
        plan_id: str = "",
        tool_id: str,
        arguments: dict[str, Any] | None = None,
        requester: AIOwnership,
        rationale: str = "",
        risk_level: str = "medium",
    ) -> ApprovalRequest:
        request = ApprovalRequest(
            approval_id="apr_" + uuid4().hex,
            task_id=str(task_id),
            plan_id=str(plan_id),
            skill_id=str(skill_id),
            tool_id=str(tool_id),
            arguments=dict(arguments or {}),
            requester=requester,
            rationale=str(rationale),
            risk_level=str(risk_level),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.store.upsert(request)
        return request

    def get(self, approval_id: str) -> ApprovalRequest:
        for request in self.store.all():
            if request.approval_id == approval_id:
                return request
        raise AdminPolicyError(f"Không tìm thấy approval request: {approval_id}")

    def pending(self) -> tuple[ApprovalRequest, ...]:
        return tuple(item for item in self.store.all() if item.status is ApprovalStatus.PENDING)

    def approve(self, approval_id: str, *, admin_actor: str, actor_owner: AIOwnership) -> ApprovalRequest:
        if actor_owner is not AIOwnership.ADMIN:
            raise AdminPolicyError("Chỉ ADMIN mới được phê duyệt approval.")
        if not str(admin_actor).strip():
            raise AdminPolicyError("ADMIN actor là bắt buộc khi phê duyệt.")
        current = self.get(approval_id)
        if current.status is not ApprovalStatus.PENDING:
            raise AdminPolicyError(f"Approval không ở trạng thái pending: {approval_id}")
        updated = replace(
            current,
            status=ApprovalStatus.APPROVED,
            decided_at=datetime.now(timezone.utc).isoformat(),
            decided_by=str(admin_actor),
            execution_token="exec_" + uuid4().hex,
        )
        self.store.upsert(updated)
        return updated

    def reject(self, approval_id: str, *, admin_actor: str, actor_owner: AIOwnership, reason: str = "") -> ApprovalRequest:
        if actor_owner is not AIOwnership.ADMIN:
            raise AdminPolicyError("Chỉ ADMIN mới được từ chối approval.")
        if not str(admin_actor).strip():
            raise AdminPolicyError("ADMIN actor là bắt buộc khi từ chối.")
        current = self.get(approval_id)
        if current.status is not ApprovalStatus.PENDING:
            raise AdminPolicyError(f"Approval không ở trạng thái pending: {approval_id}")
        updated = replace(
            current,
            status=ApprovalStatus.REJECTED,
            decided_at=datetime.now(timezone.utc).isoformat(),
            decided_by=str(admin_actor),
            rejection_reason=str(reason),
        )
        self.store.upsert(updated)
        return updated

    def authorize_execution(self, approval_id: str, execution_token: str) -> ApprovalRequest:
        current = self.get(approval_id)
        if current.status is not ApprovalStatus.APPROVED:
            raise AdminPolicyError(f"Approval chưa được ADMIN phê duyệt: {approval_id}")
        if not execution_token or execution_token != current.execution_token:
            raise AdminPolicyError("Execution token không hợp lệ.")
        return current

    def mark_executed(self, approval_id: str) -> ApprovalRequest:
        current = self.get(approval_id)
        if current.status is not ApprovalStatus.APPROVED:
            raise AdminPolicyError("Chỉ approval APPROVED mới được đánh dấu đã thực thi.")
        updated = replace(current, status=ApprovalStatus.EXECUTED)
        self.store.upsert(updated)
        return updated
