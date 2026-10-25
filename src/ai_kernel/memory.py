from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .contracts import AIOwnership
from .evaluation import EvaluationGate, EvaluationReport, EvaluationStatus, default_memory_checks
from .governance import AdminPolicyError
from .knowledge import KnowledgeRegistry


class MemoryStatus(str, Enum):
    CANDIDATE = "candidate"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    key: str
    content: str
    source: str
    skill_id: str
    content_hash: str
    status: MemoryStatus = MemoryStatus.CANDIDATE
    created_at: str = ""
    updated_at: str = ""
    approved_by: str = ""
    evaluation_id: str = ""
    quality_score: float = 0.0

    @staticmethod
    def build(*, key: str, content: str, source: str, skill_id: str = "") -> "MemoryRecord":
        normalized = str(content or "").strip()
        if not str(key or "").strip():
            raise ValueError("memory key is required")
        if not normalized:
            raise ValueError("memory content is required")
        if not str(source or "").strip():
            raise ValueError("memory source is required")
        if not str(skill_id or "").strip():
            raise ValueError("memory skill_id is required")
        now = datetime.now(timezone.utc).isoformat()
        return MemoryRecord(
            memory_id="mem_" + uuid4().hex,
            key=key.strip(),
            content=normalized,
            source=source.strip(),
            skill_id=skill_id.strip(),
            content_hash=hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
            created_at=now,
            updated_at=now,
        )


class JSONMemoryStore:
    """Local-first store for governed AI memory."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        default_path = os.getenv("MATH_TEACHER_AI_MEMORY_PATH", ".mathteacher_ai/memory_registry.json")
        self.path = Path(path or default_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> list[MemoryRecord]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        rows = payload if isinstance(payload, list) else payload.get("records", [])
        result: list[MemoryRecord] = []
        for row in rows:
            try:
                result.append(MemoryRecord(**{**row, "status": MemoryStatus(row.get("status", MemoryStatus.CANDIDATE.value))}))
            except (TypeError, ValueError):
                continue
        return result

    def _write(self, records: Iterable[MemoryRecord]) -> None:
        payload = [{**asdict(record), "status": record.status.value} for record in records]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix="memory_", suffix=".tmp", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def list_all(self) -> tuple[MemoryRecord, ...]:
        return tuple(self._read())

    def get(self, memory_id: str) -> MemoryRecord:
        for record in self._read():
            if record.memory_id == memory_id:
                return record
        raise KeyError(memory_id)

    def upsert(self, record: MemoryRecord) -> MemoryRecord:
        records = self._read()
        output = [record if item.memory_id == record.memory_id else item for item in records]
        if not any(item.memory_id == record.memory_id for item in records):
            output.append(record)
        self._write(output)
        return record


_TOKEN_RE = re.compile(r"[\wÀ-ỹ]{2,}", re.UNICODE)


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(str(text or "").casefold()))


class MemoryRegistry:
    """ADMIN-governed memory lifecycle plus deterministic retrieval."""

    def __init__(self, store: JSONMemoryStore | None = None, *, gate: EvaluationGate | None = None) -> None:
        self.store = store or JSONMemoryStore()
        self.gate = gate or EvaluationGate()

    def propose(self, record: MemoryRecord, *, owner: AIOwnership) -> MemoryRecord:
        if record.status is not MemoryStatus.CANDIDATE:
            raise ValueError("Memory proposal must start as CANDIDATE.")
        if owner not in {AIOwnership.SYSTEM, AIOwnership.USER, AIOwnership.ADMIN}:
            raise AdminPolicyError("Nguồn tạo memory không hợp lệ.")
        self.store.upsert(record)
        return record

    def evaluate(self, memory_id: str) -> EvaluationReport:
        record = self.store.get(memory_id)
        report = self.gate.evaluate(
            subject_id=record.memory_id,
            checks=default_memory_checks(content=record.content, source=record.source, skill_id=record.skill_id),
        )
        return report

    def approve(
        self,
        memory_id: str,
        *,
        owner: AIOwnership,
        approver: str = "ADMIN",
        evaluation: EvaluationReport | None = None,
    ) -> MemoryRecord:
        if owner is not AIOwnership.ADMIN:
            raise AdminPolicyError("Chỉ ADMIN được phát hành memory dùng chung.")
        record = self.store.get(memory_id)
        report = evaluation or self.evaluate(memory_id)
        if report.subject_id != memory_id:
            raise ValueError("Evaluation không thuộc memory đang approve.")
        if report.status is not EvaluationStatus.PASS:
            raise ValueError("Memory phải vượt Evaluation Gate trước khi publish.")
        now = datetime.now(timezone.utc).isoformat()
        return self.store.upsert(replace(
            record,
            status=MemoryStatus.APPROVED,
            approved_by=approver.strip() or "ADMIN",
            evaluation_id=report.evaluation_id,
            quality_score=report.score,
            updated_at=now,
        ))

    def reject(self, memory_id: str, *, owner: AIOwnership) -> MemoryRecord:
        if owner is not AIOwnership.ADMIN:
            raise AdminPolicyError("Chỉ ADMIN được từ chối memory.")
        record = self.store.get(memory_id)
        if record.status is MemoryStatus.APPROVED:
            raise ValueError("Approved memory phải được REVOKE, không REJECT.")
        return self.store.upsert(replace(record, status=MemoryStatus.REJECTED, updated_at=datetime.now(timezone.utc).isoformat()))

    def revoke(self, memory_id: str, *, owner: AIOwnership) -> MemoryRecord:
        if owner is not AIOwnership.ADMIN:
            raise AdminPolicyError("Chỉ ADMIN được thu hồi memory.")
        record = self.store.get(memory_id)
        return self.store.upsert(replace(record, status=MemoryStatus.REVOKED, updated_at=datetime.now(timezone.utc).isoformat()))

    def approved(self, *, skill_id: str = "", key: str = "") -> tuple[MemoryRecord, ...]:
        rows = [item for item in self.store.list_all() if item.status is MemoryStatus.APPROVED]
        if skill_id:
            rows = [item for item in rows if item.skill_id == skill_id]
        if key:
            rows = [item for item in rows if item.key == key]
        return tuple(rows)

    def retrieve(self, query: str, *, skill_id: str = "", limit: int = 5) -> tuple[tuple[MemoryRecord, float], ...]:
        q = _tokens(query)
        if not q:
            return ()
        scored: list[tuple[MemoryRecord, float]] = []
        for item in self.approved(skill_id=skill_id):
            overlap = q.intersection(_tokens(item.content + " " + item.key + " " + item.source))
            if not overlap:
                continue
            score = len(overlap) / max(1, len(q))
            scored.append((item, round(score, 6)))
        scored.sort(key=lambda pair: (pair[1], pair[0].quality_score), reverse=True)
        return tuple(scored[: max(1, int(limit))])

    def summary(self) -> dict[str, int]:
        counts = {status.value: 0 for status in MemoryStatus}
        for item in self.store.list_all():
            counts[item.status.value] += 1
        return counts


class AIContextRetriever:
    """Merged local RAG context from approved knowledge and approved memory."""

    def __init__(self, *, knowledge: KnowledgeRegistry, memory: MemoryRegistry) -> None:
        self.knowledge = knowledge
        self.memory = memory

    def retrieve(self, query: str, *, skill_id: str = "", limit: int = 6) -> tuple[dict[str, object], ...]:
        rows: list[tuple[float, dict[str, object]]] = []
        for record in self.knowledge.approved(skill_id=skill_id):
            overlap = _tokens(query).intersection(_tokens(record.content + " " + record.key + " " + record.source))
            if overlap:
                rows.append((len(overlap) / max(1, len(_tokens(query))), {
                    "type": "knowledge",
                    "id": record.knowledge_id,
                    "title": record.title,
                    "content": record.content,
                    "source": record.source,
                }))
        for record, score in self.memory.retrieve(query, skill_id=skill_id, limit=limit):
            rows.append((score, {
                "type": "memory",
                "id": record.memory_id,
                "content": record.content,
                "source": record.source,
                "quality_score": record.quality_score,
            }))
        rows.sort(key=lambda pair: pair[0], reverse=True)
        return tuple(item for _, item in rows[: max(1, int(limit))])
