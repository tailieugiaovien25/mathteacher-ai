"""Domain models for the NotebookLM integration boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class NotebookStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class NotebookSourceStatus(str, Enum):
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"
    REMOVED = "REMOVED"


class SyncRunStatus(str, Enum):
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class Notebook:
    notebook_id: str
    notebook_name: str
    notebook_url: str | None = None
    external_notebook_id: str | None = None
    status: NotebookStatus = NotebookStatus.ACTIVE
    metadata: dict[str, object] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class NotebookSource:
    source_id: str
    notebook_id: str
    document_id: str
    status: NotebookSourceStatus = NotebookSourceStatus.PENDING
    external_source_id: str | None = None
    last_synced_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class SyncRun:
    sync_run_id: str
    notebook_id: str
    status: SyncRunStatus
    started_at: datetime
    finished_at: datetime | None = None
    source_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    error_message: str | None = None