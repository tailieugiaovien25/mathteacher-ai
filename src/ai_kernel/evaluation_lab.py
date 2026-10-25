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
from .memory import MemoryRecord, MemoryRegistry


class EvaluationOutcome(str, Enum):
    ACCEPTED = "accepted"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


@dataclass(frozen=True)
class EvaluationRun:
    run_id: str
    task_id: str
    skill_id: str
    input_fingerprint: str
    result_fingerprint: str
    outcome: EvaluationOutcome
    score: float
    summary: str = ""
    audit_id: str = ""
    created_at: str = ""


@dataclass(frozen=True)
class EvaluationFeedback:
    feedback_id: str
    run_id: str
    outcome: EvaluationOutcome
    reason_code: str
    comment: str = ""
    reviewer: str = ""
    created_at: str = ""


class JSONEvaluationLabStore:
    """Local-first immutable-ish event store for AI evaluations and feedback."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = Path(path or os.getenv("MATH_TEACHER_AI_EVALUATION_STORE", "data/ai/evaluation_lab.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"runs": [], "feedback": []})

    def _read(self) -> dict[str, list[dict[str, object]]]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return {"runs": [], "feedback": []}
            return {
                "runs": list(payload.get("runs") or []),
                "feedback": list(payload.get("feedback") or []),
            }
        except (OSError, json.JSONDecodeError):
            return {"runs": [], "feedback": []}

    def _write(self, payload: dict[str, list[dict[str, object]]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix="evaluation-lab-", suffix=".json", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def add_run(self, run: EvaluationRun) -> EvaluationRun:
        payload = self._read()
        payload["runs"].append(asdict(run) | {"outcome": run.outcome.value})
        self._write(payload)
        return run

    def add_feedback(self, feedback: EvaluationFeedback) -> EvaluationFeedback:
        payload = self._read()
        payload["feedback"].append(asdict(feedback) | {"outcome": feedback.outcome.value})
        self._write(payload)
        return feedback

    def runs(self) -> tuple[EvaluationRun, ...]:
        output: list[EvaluationRun] = []
        for row in self._read()["runs"]:
            try:
                output.append(
                    EvaluationRun(
                        run_id=str(row["run_id"]), task_id=str(row["task_id"]), skill_id=str(row["skill_id"]),
                        input_fingerprint=str(row["input_fingerprint"]), result_fingerprint=str(row["result_fingerprint"]),
                        outcome=EvaluationOutcome(str(row["outcome"])), score=float(row.get("score", 0.0)),
                        summary=str(row.get("summary", "")), audit_id=str(row.get("audit_id", "")),
                        created_at=str(row.get("created_at", "")),
                    )
                )
            except (KeyError, ValueError, TypeError):
                continue
        return tuple(output)

    def feedback(self) -> tuple[EvaluationFeedback, ...]:
        output: list[EvaluationFeedback] = []
        for row in self._read()["feedback"]:
            try:
                output.append(
                    EvaluationFeedback(
                        feedback_id=str(row["feedback_id"]), run_id=str(row["run_id"]),
                        outcome=EvaluationOutcome(str(row["outcome"])), reason_code=str(row["reason_code"]),
                        comment=str(row.get("comment", "")), reviewer=str(row.get("reviewer", "")),
                        created_at=str(row.get("created_at", "")),
                    )
                )
            except (KeyError, ValueError, TypeError):
                continue
        return tuple(output)


class EvaluationLab:
    """Evaluation and feedback loop. It proposes learning; it never publishes learning."""

    def __init__(self, store: JSONEvaluationLabStore | None = None) -> None:
        self.store = store or JSONEvaluationLabStore()

    @staticmethod
    def _fingerprint(value: object) -> str:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def record_run(
        self,
        *,
        task_id: str,
        skill_id: str,
        input_data: object,
        result_data: object,
        outcome: EvaluationOutcome,
        score: float,
        summary: str = "",
        audit_id: str = "",
    ) -> EvaluationRun:
        score_value = float(score)
        if not 0.0 <= score_value <= 1.0:
            raise ValueError("score must be between 0 and 1")
        now = datetime.now(timezone.utc).isoformat()
        return self.store.add_run(EvaluationRun(
            run_id="run_" + uuid4().hex,
            task_id=str(task_id),
            skill_id=str(skill_id),
            input_fingerprint=self._fingerprint(input_data),
            result_fingerprint=self._fingerprint(result_data),
            outcome=outcome,
            score=score_value,
            summary=str(summary),
            audit_id=str(audit_id),
            created_at=now,
        ))

    def add_feedback(
        self,
        *,
        run_id: str,
        outcome: EvaluationOutcome,
        reason_code: str,
        reviewer: str,
        owner: AIOwnership,
        comment: str = "",
    ) -> EvaluationFeedback:
        if owner not in {AIOwnership.ADMIN, AIOwnership.USER, AIOwnership.SYSTEM}:
            raise AdminPolicyError("Nguồn feedback không hợp lệ.")
        if not str(reason_code or "").strip():
            raise ValueError("reason_code is required")
        if not any(item.run_id == run_id for item in self.store.runs()):
            raise ValueError("run_id không tồn tại trong Evaluation Lab")
        return self.store.add_feedback(EvaluationFeedback(
            feedback_id="fb_" + uuid4().hex,
            run_id=run_id,
            outcome=outcome,
            reason_code=str(reason_code).strip(),
            comment=str(comment).strip(),
            reviewer=str(reviewer).strip() or owner.value,
            created_at=datetime.now(timezone.utc).isoformat(),
        ))

    def summary(self, *, skill_id: str = "") -> dict[str, int | float]:
        runs = [item for item in self.store.runs() if not skill_id or item.skill_id == skill_id]
        if not runs:
            return {"runs": 0, "accepted": 0, "needs_review": 0, "rejected": 0, "average_score": 0.0}
        return {
            "runs": len(runs),
            "accepted": sum(item.outcome is EvaluationOutcome.ACCEPTED for item in runs),
            "needs_review": sum(item.outcome is EvaluationOutcome.NEEDS_REVIEW for item in runs),
            "rejected": sum(item.outcome is EvaluationOutcome.REJECTED for item in runs),
            "average_score": round(sum(item.score for item in runs) / len(runs), 6),
        }

    def propose_memory_candidates(
        self,
        *,
        skill_id: str,
        min_feedback: int = 2,
        reason_code: str = "",
        memory_registry: MemoryRegistry | None = None,
    ) -> tuple[MemoryRecord, ...]:
        """Turn repeated feedback patterns into CANDIDATE memory only."""
        runs = {item.run_id: item for item in self.store.runs() if item.skill_id == skill_id}
        feedback = [item for item in self.store.feedback() if item.run_id in runs]
        grouped: dict[str, list[EvaluationFeedback]] = {}
        for item in feedback:
            if reason_code and item.reason_code != reason_code:
                continue
            grouped.setdefault(item.reason_code, []).append(item)

        candidates: list[MemoryRecord] = []
        for code, rows in grouped.items():
            if len(rows) < max(1, int(min_feedback)):
                continue
            relevant_runs = [runs[item.run_id] for item in rows]
            pattern_key = f"{skill_id}:{code}"
            content = (
                f"Đúc kết từ {len(rows)} phản hồi cho skill {skill_id}. "
                f"Mẫu vấn đề: {code}. "
                "Đây là tri thức ứng viên từ dữ liệu đánh giá, chưa phải quy tắc chính thức."
            )
            source = f"evaluation_lab:{pattern_key}"
            record = MemoryRecord.build(
                key=f"feedback_pattern:{pattern_key}",
                content=content,
                source=source,
                skill_id=skill_id,
            )
            # Keep evidence deterministic and auditable without promoting the candidate.
            record = replace(record, quality_score=round(sum(item.score for item in relevant_runs) / len(relevant_runs), 6))
            if memory_registry is not None:
                memory_registry.propose(record, owner=AIOwnership.SYSTEM)
            candidates.append(record)
        return tuple(candidates)
