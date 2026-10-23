from __future__ import annotations

import json
import os
import tempfile
import threading
from contextlib import contextmanager
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
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"
    REJECTED = "rejected"
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

    _locks: dict[str, threading.RLock] = {}
    _locks_guard = threading.Lock()

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = Path(path or os.getenv("MATH_TEACHER_AI_APPROVALS", ".mathteacher_ai/approval_queue.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.path.with_name(self.path.name + ".lock")
        if not self.path.exists():
            self._write([])

    @property
    def _process_lock(self) -> threading.RLock:
        key = str(self.lock_path.resolve())
        with self._locks_guard:
            return self._locks.setdefault(key, threading.RLock())

    @contextmanager
    def _file_lock(self):
        """
        Cross-process lock for the approval JSON transition.

        Windows uses msvcrt.locking; POSIX uses fcntl.flock.
        The process-local RLock prevents competing threads in the same
        Python process from entering the transition simultaneously.
        """
        with self._process_lock:
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            self.lock_path.touch(exist_ok=True)

            with self.lock_path.open("r+b") as handle:
                if os.name == "nt":
                    import msvcrt

                    handle.seek(0, os.SEEK_END)
                    if handle.tell() == 0:
                        handle.write(b"0")
                        handle.flush()

                    handle.seek(0)
                    msvcrt.locking(
                        handle.fileno(),
                        msvcrt.LK_LOCK,
                        1,
                    )
                    try:
                        yield
                    finally:
                        handle.seek(0)
                        msvcrt.locking(
                            handle.fileno(),
                            msvcrt.LK_UNLCK,
                            1,
                        )
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                    try:
                        yield
                    finally:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _read(self) -> list[dict[str, Any]]:
        try:
            raw = self.path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AdminPolicyError(
                "Cannot read approval queue; refusing to overwrite existing approvals."
            ) from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AdminPolicyError(
                "Approval queue JSON is invalid; refusing to overwrite existing approvals."
            ) from exc

        if not isinstance(payload, list):
            raise AdminPolicyError(
                "Approval queue must contain a JSON list; refusing to overwrite existing approvals."
            )

        if not all(isinstance(row, dict) for row in payload):
            raise AdminPolicyError(
                "Approval queue contains invalid records; refusing to overwrite existing approvals."
            )

        return payload
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
                       "requester": AIOwnership(row.get("requester", AIOwnership.USER.value))}
                ))
            except (TypeError, ValueError):
                continue
        return tuple(result)

    def upsert(self, request: ApprovalRequest) -> None:
        with self._file_lock():
            rows = self._read()
            payload = asdict(request) | {
                "status": request.status.value,
                "requester": request.requester.value,
            }
            replaced = False
            for idx, row in enumerate(rows):
                if row.get("approval_id") == request.approval_id:
                    rows[idx] = payload
                    replaced = True
                    break
            if not replaced:
                rows.append(payload)
            self._write(rows)

    def decide(
        self,
        approval_id: str,
        *,
        decision: str,
        admin_actor: str,
        execution_token: str = "",
        rejection_reason: str = "",
    ) -> ApprovalRequest:
        """Atomically decide a pending approval across threads/processes."""
        if decision not in {"approve", "reject"}:
            raise AdminPolicyError("Quyết định approval không hợp lệ.")
        if not str(admin_actor).strip():
            raise AdminPolicyError("ADMIN actor là bắt buộc.")

        with self._file_lock():
            rows = self._read()
            target_index = None
            current = None

            for idx, row in enumerate(rows):
                if row.get("approval_id") != approval_id:
                    continue
                try:
                    current = ApprovalRequest(
                        **{
                            **row,
                            "status": ApprovalStatus(
                                row.get("status", ApprovalStatus.PENDING.value)
                            ),
                            "requester": AIOwnership(
                                row.get("requester", AIOwnership.USER.value)
                            ),
                        }
                    )
                except (TypeError, ValueError) as exc:
                    raise AdminPolicyError(
                        f"Approval request không hợp lệ: {approval_id}"
                    ) from exc
                target_index = idx
                break

            if current is None or target_index is None:
                raise AdminPolicyError(
                    f"Không tìm thấy approval request: {approval_id}"
                )
            if current.status is not ApprovalStatus.PENDING:
                raise AdminPolicyError(
                    f"Approval không ở trạng thái pending: {approval_id}"
                )

            approved = decision == "approve"
            updated = replace(
                current,
                status=(
                    ApprovalStatus.APPROVED
                    if approved
                    else ApprovalStatus.REJECTED
                ),
                decided_at=datetime.now(timezone.utc).isoformat(),
                decided_by=str(admin_actor),
                execution_token=execution_token if approved else "",
                rejection_reason="" if approved else str(rejection_reason),
            )
            rows[target_index] = asdict(updated) | {
                "status": updated.status.value,
                "requester": updated.requester.value,
            }
            self._write(rows)
            return updated

    def claim_execution(
        self,
        approval_id: str,
        execution_token: str,
    ) -> ApprovalRequest:
        """
        Atomically consume an APPROVED execution token.

        Only the first caller can transition APPROVED -> EXECUTING.
        """
        with self._file_lock():
            rows = self._read()

            target_index = None
            current: ApprovalRequest | None = None

            for idx, row in enumerate(rows):
                if row.get("approval_id") != approval_id:
                    continue
                try:
                    current = ApprovalRequest(
                        **{
                            **row,
                            "status": ApprovalStatus(
                                row.get(
                                    "status",
                                    ApprovalStatus.PENDING.value,
                                )
                            ),
                            "requester": AIOwnership(
                                row.get(
                                    "requester",
                                    AIOwnership.USER.value,
                                )
                            ),
                        }
                    )
                except (TypeError, ValueError) as exc:
                    raise AdminPolicyError(
                        f"Approval request không hợp lệ: {approval_id}"
                    ) from exc
                target_index = idx
                break

            if current is None or target_index is None:
                raise AdminPolicyError(
                    f"Không tìm thấy approval request: {approval_id}"
                )

            if current.status is not ApprovalStatus.APPROVED:
                raise AdminPolicyError(
                    f"Approval không sẵn sàng để thực thi: {approval_id}"
                )

            if not execution_token or execution_token != current.execution_token:
                raise AdminPolicyError("Execution token không hợp lệ.")

            updated = replace(
                current,
                status=ApprovalStatus.EXECUTING,
            )

            rows[target_index] = asdict(updated) | {
                "status": updated.status.value,
                "requester": updated.requester.value,
            }
            self._write(rows)
            return updated

    def transition_status(
        self,
        approval_id: str,
        *,
        expected_status: ApprovalStatus,
        new_status: ApprovalStatus,
    ) -> ApprovalRequest:
        with self._file_lock():
            rows = self._read()

            for idx, row in enumerate(rows):
                if row.get("approval_id") != approval_id:
                    continue

                try:
                    current = ApprovalRequest(
                        **{
                            **row,
                            "status": ApprovalStatus(
                                row.get(
                                    "status",
                                    ApprovalStatus.PENDING.value,
                                )
                            ),
                            "requester": AIOwnership(
                                row.get(
                                    "requester",
                                    AIOwnership.USER.value,
                                )
                            ),
                        }
                    )
                except (TypeError, ValueError) as exc:
                    raise AdminPolicyError(
                        f"Approval request không hợp lệ: {approval_id}"
                    ) from exc

                if current.status is not expected_status:
                    raise AdminPolicyError(
                        f"Approval không ở trạng thái "
                        f"{expected_status.value}: {approval_id}"
                    )

                updated = replace(current, status=new_status)
                rows[idx] = asdict(updated) | {
                    "status": updated.status.value,
                    "requester": updated.requester.value,
                }
                self._write(rows)
                return updated

            raise AdminPolicyError(
                f"Không tìm thấy approval request: {approval_id}"
            )


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
        return self.store.decide(
            approval_id,
            decision="approve",
            admin_actor=str(admin_actor),
            execution_token="exec_" + uuid4().hex,
        )

    def reject(self, approval_id: str, *, admin_actor: str, actor_owner: AIOwnership, reason: str = "") -> ApprovalRequest:
        if actor_owner is not AIOwnership.ADMIN:
            raise AdminPolicyError("Chỉ ADMIN mới được từ chối approval.")
        if not str(admin_actor).strip():
            raise AdminPolicyError("ADMIN actor là bắt buộc khi từ chối.")
        return self.store.decide(
            approval_id,
            decision="reject",
            admin_actor=str(admin_actor),
            rejection_reason=str(reason),
        )

    def authorize_execution(
        self, approval_id: str, execution_token: str
    ) -> ApprovalRequest:
        current = self.get(approval_id)
        if current.status is not ApprovalStatus.APPROVED:
            raise AdminPolicyError(
                f"Approval chưa được ADMIN phê duyệt: {approval_id}"
            )
        if not execution_token or execution_token != current.execution_token:
            raise AdminPolicyError("Execution token không hợp lệ.")
        return current

    def claim_execution(
        self, approval_id: str, execution_token: str
    ) -> ApprovalRequest:
        """Atomically consume an approved execution token exactly once."""
        return self.store.claim_execution(approval_id, execution_token)

    def mark_executed(self, approval_id: str) -> ApprovalRequest:
        return self.store.transition_status(
            approval_id,
            expected_status=ApprovalStatus.EXECUTING,
            new_status=ApprovalStatus.EXECUTED,
        )

    def mark_failed(self, approval_id: str) -> ApprovalRequest:
        return self.store.transition_status(
            approval_id,
            expected_status=ApprovalStatus.EXECUTING,
            new_status=ApprovalStatus.FAILED,
        )
