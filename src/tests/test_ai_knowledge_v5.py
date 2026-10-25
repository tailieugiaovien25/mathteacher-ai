from __future__ import annotations

from pathlib import Path

import pytest

from ai_kernel import AIOwnership
from ai_kernel.knowledge import JSONKnowledgeStore, KnowledgeRecord, KnowledgeRegistry, KnowledgeStatus
from ai_kernel.governance import AdminPolicyError


def _registry(tmp_path: Path) -> KnowledgeRegistry:
    return KnowledgeRegistry(JSONKnowledgeStore(tmp_path / "knowledge.json"))


def test_ai_can_propose_but_cannot_publish(tmp_path: Path):
    registry = _registry(tmp_path)
    record = KnowledgeRecord.build(
        key="math.grade6.presentation",
        title="Quy tắc trình bày Toán 6",
        content="Dùng Times New Roman cho nội dung văn bản.",
        source="approved-school-rule",
        skill_id="document.standardization.audit",
    )
    registry.propose(record, owner=AIOwnership.SYSTEM)
    with pytest.raises(AdminPolicyError):
        registry.approve(record.knowledge_id, owner=AIOwnership.USER)
    assert registry.store.get(record.knowledge_id).status is KnowledgeStatus.CANDIDATE


def test_admin_can_approve_and_only_approved_is_retrievable(tmp_path: Path):
    registry = _registry(tmp_path)
    record = KnowledgeRecord.build(
        key="math.grade6.presentation",
        title="Quy tắc trình bày Toán 6",
        content="Lề trái 3 cm.",
        source="approved-school-rule",
    )
    registry.propose(record, owner=AIOwnership.SYSTEM)
    registry.approve(record.knowledge_id, owner=AIOwnership.ADMIN)
    approved = registry.approved(key=record.key)
    assert len(approved) == 1
    assert approved[0].knowledge_id == record.knowledge_id


def test_revoke_removes_knowledge_from_ai_context(tmp_path: Path):
    registry = _registry(tmp_path)
    record = KnowledgeRecord.build(
        key="doc.standardization.rule",
        title="Không đổi nội dung",
        content="Chuẩn hóa hình thức không được thay đổi nội dung.",
        source="mathteacher-policy",
    )
    registry.propose(record, owner=AIOwnership.SYSTEM)
    registry.approve(record.knowledge_id, owner=AIOwnership.ADMIN)
    registry.revoke(record.knowledge_id, owner=AIOwnership.ADMIN)
    assert registry.approved() == ()


def test_store_survives_new_registry_instance(tmp_path: Path):
    path = tmp_path / "knowledge.json"
    first = KnowledgeRegistry(JSONKnowledgeStore(path))
    record = KnowledgeRecord.build(
        key="standardization.integrity",
        title="Fingerprint bất biến",
        content="Văn bản trước và sau phải được kiểm tra bằng fingerprint.",
        source="mathteacher-kernel",
    )
    first.propose(record, owner=AIOwnership.SYSTEM)
    first.approve(record.knowledge_id, owner=AIOwnership.ADMIN)

    second = KnowledgeRegistry(JSONKnowledgeStore(path))
    loaded = second.approved()
    assert len(loaded) == 1
    assert loaded[0].content_hash == record.content_hash


def test_summary_counts_lifecycle(tmp_path: Path):
    registry = _registry(tmp_path)
    candidate = KnowledgeRecord.build(
        key="k1", title="Candidate", content="A", source="test"
    )
    registry.propose(candidate, owner=AIOwnership.SYSTEM)
    approved = KnowledgeRecord.build(
        key="k2", title="Approved", content="B", source="test"
    )
    registry.propose(approved, owner=AIOwnership.SYSTEM)
    registry.approve(approved.knowledge_id, owner=AIOwnership.ADMIN)
    counts = registry.summary()
    assert counts[KnowledgeStatus.CANDIDATE.value] == 1
    assert counts[KnowledgeStatus.APPROVED.value] == 1
