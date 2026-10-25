from __future__ import annotations

from pathlib import Path

import pytest

from ai_kernel import (
    AIOwnership,
    EvaluationOutcome,
    EvaluationLab,
    JSONEvaluationLabStore,
    MemoryRegistry,
)


def _lab(tmp_path: Path) -> EvaluationLab:
    return EvaluationLab(JSONEvaluationLabStore(tmp_path / "evaluation.json"))


def test_record_and_feedback(tmp_path: Path):
    lab = _lab(tmp_path)
    run = lab.record_run(
        task_id="std-1",
        skill_id="document.standardization.audit",
        input_data={"before": {"font": "Arial"}},
        result_data={"after": {"font": "Times New Roman"}},
        outcome=EvaluationOutcome.ACCEPTED,
        score=0.95,
    )
    feedback = lab.add_feedback(
        run_id=run.run_id,
        outcome=EvaluationOutcome.ACCEPTED,
        reason_code="format_fixed",
        reviewer="teacher",
        owner=AIOwnership.USER,
    )
    assert feedback.run_id == run.run_id
    assert lab.summary()["runs"] == 1


def test_feedback_requires_existing_run(tmp_path: Path):
    lab = _lab(tmp_path)
    with pytest.raises(ValueError):
        lab.add_feedback(
            run_id="missing",
            outcome=EvaluationOutcome.REJECTED,
            reason_code="bad",
            reviewer="teacher",
            owner=AIOwnership.USER,
        )


def test_repeated_feedback_creates_candidate_only(tmp_path: Path):
    lab = _lab(tmp_path)
    memory = MemoryRegistry()
    for idx in range(2):
        run = lab.record_run(
            task_id=f"std-{idx}",
            skill_id="document.standardization.audit",
            input_data={"idx": idx},
            result_data={"status": "review"},
            outcome=EvaluationOutcome.NEEDS_REVIEW,
            score=0.6,
        )
        lab.add_feedback(
            run_id=run.run_id,
            outcome=EvaluationOutcome.NEEDS_REVIEW,
            reason_code="table_split",
            reviewer="teacher",
            owner=AIOwnership.USER,
        )
    candidates = lab.propose_memory_candidates(
        skill_id="document.standardization.audit",
        min_feedback=2,
        reason_code="table_split",
        memory_registry=memory,
    )
    assert len(candidates) == 1
    assert candidates[0].status.value == "candidate"
    assert memory.approved(skill_id="document.standardization.audit") == ()


def test_candidate_never_contains_governance_instruction(tmp_path: Path):
    lab = _lab(tmp_path)
    run_ids = []
    for idx in range(2):
        run = lab.record_run(
            task_id=f"std-{idx}",
            skill_id="document.standardization.audit",
            input_data={"idx": idx},
            result_data={"status": "rejected"},
            outcome=EvaluationOutcome.REJECTED,
            score=0.2,
        )
        run_ids.append(run.run_id)
        lab.add_feedback(
            run_id=run.run_id,
            outcome=EvaluationOutcome.REJECTED,
            reason_code="manual_review",
            reviewer="ADMIN",
            owner=AIOwnership.ADMIN,
        )
    candidates = lab.propose_memory_candidates(
        skill_id="document.standardization.audit",
        min_feedback=2,
        reason_code="manual_review",
    )
    assert len(candidates) == 1
    lowered = candidates[0].content.casefold()
    assert "self_modify_kernel" not in lowered
    assert "grant_admin" not in lowered
    assert "change_governance" not in lowered


def test_skill_scoping(tmp_path: Path):
    lab = _lab(tmp_path)
    for idx, skill in enumerate(("document.standardization.audit", "lesson.authoring.assistant")):
        run = lab.record_run(
            task_id=f"task-{idx}",
            skill_id=skill,
            input_data={"idx": idx},
            result_data={"ok": True},
            outcome=EvaluationOutcome.ACCEPTED,
            score=0.9,
        )
        lab.add_feedback(
            run_id=run.run_id,
            outcome=EvaluationOutcome.ACCEPTED,
            reason_code="good",
            reviewer="teacher",
            owner=AIOwnership.USER,
        )
    candidates = lab.propose_memory_candidates(
        skill_id="document.standardization.audit",
        min_feedback=1,
        reason_code="good",
    )
    assert len(candidates) == 1
    assert candidates[0].skill_id == "document.standardization.audit"
