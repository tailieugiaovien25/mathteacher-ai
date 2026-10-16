from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SyncState(str, Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"


@dataclass(frozen=True)
class KnowledgeSyncStatus:
    document_id: str
    target: str
    state: SyncState = SyncState.PENDING
    message: str | None = None
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class KnowledgeSyncRegistry:
    """Tracks synchronization state without touching source documents."""

    def __init__(self) -> None:
        self._statuses: dict[tuple[str, str], KnowledgeSyncStatus] = {}

    def set_status(
        self,
        document_id: str,
        target: str,
        state: SyncState,
        message: str | None = None,
    ) -> KnowledgeSyncStatus:
        status = KnowledgeSyncStatus(
            document_id=document_id,
            target=target,
            state=state,
            message=message,
        )
        self._statuses[(document_id, target)] = status
        return status

    def get_status(
        self,
        document_id: str,
        target: str,
    ) -> KnowledgeSyncStatus | None:
        return self._statuses.get((document_id, target))

    def list_statuses(
        self,
        document_id: str | None = None,
    ) -> tuple[KnowledgeSyncStatus, ...]:
        statuses = tuple(self._statuses.values())
        if document_id is None:
            return statuses
        return tuple(
            status
            for status in statuses
            if status.document_id == document_id
        )
