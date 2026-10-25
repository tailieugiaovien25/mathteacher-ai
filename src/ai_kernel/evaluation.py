from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable
from uuid import uuid4


class EvaluationStatus(str, Enum):
    PASS = "pass"
    REVIEW = "review"
    FAIL = "fail"


class EvaluationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True)
class EvaluationCheck:
    code: str
    passed: bool
    weight: float = 1.0
    severity: EvaluationSeverity = EvaluationSeverity.WARNING
    message: str = ""


@dataclass(frozen=True)
class EvaluationReport:
    evaluation_id: str
    status: EvaluationStatus
    score: float
    threshold: float
    checks: tuple[EvaluationCheck, ...]
    subject_id: str = ""
    created_at: str = ""


class EvaluationGate:
    """Deterministic gate used before knowledge/memory enters shared AI context.

    The gate is deliberately model-independent: an LLM may propose evidence, but
    this object decides whether the evidence is structurally sufficient.
    """

    def __init__(self, *, threshold: float = 0.80) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        self.threshold = threshold

    def evaluate(
        self,
        *,
        subject_id: str,
        checks: Iterable[EvaluationCheck],
    ) -> EvaluationReport:
        rows = tuple(checks)
        total_weight = sum(max(0.0, float(item.weight)) for item in rows)
        passed_weight = sum(max(0.0, float(item.weight)) for item in rows if item.passed)
        score = 1.0 if total_weight == 0 else passed_weight / total_weight
        critical_fail = any(
            (not item.passed) and item.severity is EvaluationSeverity.CRITICAL
            for item in rows
        )
        status = EvaluationStatus.FAIL if critical_fail else (
            EvaluationStatus.PASS if score >= self.threshold else EvaluationStatus.REVIEW
        )
        return EvaluationReport(
            evaluation_id="eval_" + uuid4().hex,
            status=status,
            score=round(score, 6),
            threshold=self.threshold,
            checks=rows,
            subject_id=subject_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def require_pass(self, report: EvaluationReport) -> EvaluationReport:
        if report.status is not EvaluationStatus.PASS:
            raise ValueError(
                f"Evaluation gate chưa đạt PASS: {report.status.value} ({report.score:.3f})."
            )
        return report


def default_memory_checks(*, content: str, source: str, skill_id: str = "") -> tuple[EvaluationCheck, ...]:
    """Baseline checks for candidate memory/knowledge records."""
    text = str(content or "").strip()
    src = str(source or "").strip()
    skill = str(skill_id or "").strip()
    return (
        EvaluationCheck(
            "content_present",
            bool(text),
            weight=0.35,
            severity=EvaluationSeverity.CRITICAL,
            message="Memory phải có nội dung.",
        ),
        EvaluationCheck(
            "source_present",
            bool(src),
            weight=0.20,
            severity=EvaluationSeverity.CRITICAL,
            message="Memory phải có nguồn.",
        ),
        EvaluationCheck(
            "skill_scope_present",
            bool(skill),
            weight=0.15,
            severity=EvaluationSeverity.WARNING,
            message="Nên gắn memory với skill để kiểm soát phạm vi.",
        ),
        EvaluationCheck(
            "no_embedded_governance",
            not any(token in text.casefold() for token in ("self_modify_kernel", "grant_admin", "change_governance")),
            weight=0.30,
            severity=EvaluationSeverity.CRITICAL,
            message="Memory không được chứa chỉ thị tự nâng quyền hoặc sửa governance.",
        ),
    )
