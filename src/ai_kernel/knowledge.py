from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .contracts import AIOwnership
from .governance import AdminPolicyError


class KnowledgeStatus(str, Enum):
    CANDIDATE = "candidate"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"


@dataclass(frozen=True)
class KnowledgeRecord:
    knowledge_id: str
    key: str
    title: str
    content: str
    source: str
    content_hash: str
    status: KnowledgeStatus = KnowledgeStatus.CANDIDATE
    version: int = 1
    skill_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    approved_by: str = ""

    @staticmethod
    def build(*, key: str, title: str, content: str, source: str, skill_id: str = "", version: int = 1) -> "KnowledgeRecord":
        normalized = content.strip()
        if not key.strip():
            raise ValueError("knowledge key is required")
        if not title.strip():
            raise ValueError("knowledge title is required")
        if not normalized:
            raise ValueError("knowledge content is required")
        if not source.strip():
            raise ValueError("knowledge source is required")
        now = datetime.now(timezone.utc).isoformat()
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return KnowledgeRecord(
            knowledge_id="knw_" + uuid4().hex,
            key=key.strip(),
            title=title.strip(),
            content=normalized,
            source=source.strip(),
            content_hash=digest,
            status=KnowledgeStatus.CANDIDATE,
            version=max(1, int(version)),
            skill_id=skill_id.strip(),
            created_at=now,
            updated_at=now,
        )


class JSONKnowledgeStore:
    """Local-first versioned store. Storage is data; policy remains in Kernel."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        default_path = os.getenv(
            "MATH_TEACHER_AI_KNOWLEDGE_PATH",
            ".mathteacher_ai/knowledge_registry.json",
        )
        self.path = Path(path or default_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> list[KnowledgeRecord]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        rows = payload if isinstance(payload, list) else payload.get("records", [])
        result: list[KnowledgeRecord] = []
        for row in rows:
            try:
                result.append(
                    KnowledgeRecord(
                        **{
                            **row,
                            "status": KnowledgeStatus(row.get("status", KnowledgeStatus.CANDIDATE.value)),
                        }
                    )
                )
            except (TypeError, ValueError):
                continue
        return result

    def _write(self, records: Iterable[KnowledgeRecord]) -> None:
        payload = [
            {
                **asdict(record),
                "status": record.status.value,
            }
            for record in records
        ]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix="knowledge_", suffix=".tmp", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
            os.replace(tmp_name, self.path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    def list_all(self) -> tuple[KnowledgeRecord, ...]:
        return tuple(self._read())

    def get(self, knowledge_id: str) -> KnowledgeRecord:
        for record in self._read():
            if record.knowledge_id == knowledge_id:
                return record
        raise KeyError(knowledge_id)

    def upsert(self, record: KnowledgeRecord) -> KnowledgeRecord:
        records = self._read()
        replaced = False
        output: list[KnowledgeRecord] = []
        for existing in records:
            if existing.knowledge_id == record.knowledge_id:
                output.append(record)
                replaced = True
            else:
                output.append(existing)
        if not replaced:
            output.append(record)
        self._write(output)
        return record


class KnowledgeRegistry:
    """ADMIN-governed knowledge lifecycle; AI can propose, ADMIN alone can publish."""

    def __init__(self, store: JSONKnowledgeStore | None = None) -> None:
        self.store = store or JSONKnowledgeStore()

    def propose(
        self,
        record: KnowledgeRecord,
        *,
        owner: AIOwnership,
    ) -> KnowledgeRecord:
        if owner not in {AIOwnership.SYSTEM, AIOwnership.USER, AIOwnership.ADMIN}:
            raise AdminPolicyError("Nguồn tạo tri thức không hợp lệ.")
        if record.status is not KnowledgeStatus.CANDIDATE:
            raise ValueError("Knowledge proposal must start as CANDIDATE.")
        self.store.upsert(record)
        return record

    def approve(self, knowledge_id: str, *, owner: AIOwnership, approver: str = "ADMIN") -> KnowledgeRecord:
        if owner is not AIOwnership.ADMIN:
            raise AdminPolicyError("Chỉ ADMIN được phát hành tri thức dùng chung.")
        record = self.store.get(knowledge_id)
        if record.status not in {KnowledgeStatus.CANDIDATE, KnowledgeStatus.REJECTED, KnowledgeStatus.REVOKED}:
            raise ValueError(f"Không thể approve knowledge ở trạng thái {record.status.value}.")
        now = datetime.now(timezone.utc).isoformat()
        updated = replace(
            record,
            status=KnowledgeStatus.APPROVED,
            approved_by=approver.strip() or "ADMIN",
            updated_at=now,
        )
        return self.store.upsert(updated)

    def reject(self, knowledge_id: str, *, owner: AIOwnership) -> KnowledgeRecord:
        if owner is not AIOwnership.ADMIN:
            raise AdminPolicyError("Chỉ ADMIN được từ chối tri thức dùng chung.")
        record = self.store.get(knowledge_id)
        if record.status is KnowledgeStatus.APPROVED:
            raise ValueError("Approved knowledge phải được REVOKE/SUPERSEDE, không REJECT.")
        updated = replace(
            record,
            status=KnowledgeStatus.REJECTED,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        return self.store.upsert(updated)

    def revoke(self, knowledge_id: str, *, owner: AIOwnership) -> KnowledgeRecord:
        if owner is not AIOwnership.ADMIN:
            raise AdminPolicyError("Chỉ ADMIN được thu hồi tri thức.")
        record = self.store.get(knowledge_id)
        updated = replace(
            record,
            status=KnowledgeStatus.REVOKED,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        return self.store.upsert(updated)

    def supersede(self, old_id: str, new_record: KnowledgeRecord, *, owner: AIOwnership) -> KnowledgeRecord:
        if owner is not AIOwnership.ADMIN:
            raise AdminPolicyError("Chỉ ADMIN được thay thế phiên bản tri thức.")
        old = self.store.get(old_id)
        if old.key != new_record.key:
            raise ValueError("Knowledge key phải giống nhau khi supersede.")
        self.store.upsert(
            replace(old, status=KnowledgeStatus.SUPERSEDED, updated_at=datetime.now(timezone.utc).isoformat())
        )
        return self.store.upsert(new_record)

    def approved(
        self,
        *,
        skill_id: str = "",
        key: str = "",
    ) -> tuple[KnowledgeRecord, ...]:
        rows = [record for record in self.store.list_all() if record.status is KnowledgeStatus.APPROVED]
        if skill_id:
            rows = [record for record in rows if record.skill_id in {"", skill_id}]
        if key:
            rows = [record for record in rows if record.key == key]
        return tuple(rows)

    def summary(self) -> dict[str, int]:
        counts = {status.value: 0 for status in KnowledgeStatus}
        for record in self.store.list_all():
            counts[record.status.value] += 1
        return counts
