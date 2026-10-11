"""Supabase repositories for the NotebookLM bridge."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from notebooklm_bridge.models import (
    Notebook,
    NotebookSource,
    NotebookSourceStatus,
    NotebookStatus,
    SyncRun,
    SyncRunStatus,
)


class SupabaseNotebookRepository:
    """User-scoped repository for Notebook records."""

    def __init__(
        self,
        client: Any,
        user_id: str,
        table_name: str = "notebooklm_notebooks",
    ) -> None:
        self._client = client
        self._user_id = self._required_text(user_id, "user_id")
        self._table_name = self._required_text(table_name, "table_name")

    def save(self, notebook: Notebook) -> Notebook:
        response = (
            self._client.table(self._table_name)
            .upsert(
                self._to_row(notebook),
                on_conflict="user_id,notebook_id",
            )
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Supabase notebook save returned no data"
            )

        return self._from_row(response.data[0])

    def get(self, notebook_id: str) -> Notebook | None:
        response = (
            self._client.table(self._table_name)
            .select("*")
            .eq("user_id", self._user_id)
            .eq("notebook_id", notebook_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return self._from_row(response.data[0])

    def list_all(self) -> tuple[Notebook, ...]:
        response = (
            self._client.table(self._table_name)
            .select("*")
            .eq("user_id", self._user_id)
            .order("created_at", desc=True)
            .execute()
        )

        return tuple(
            self._from_row(row)
            for row in (response.data or [])
        )

    def delete(self, notebook_id: str) -> bool:
        response = (
            self._client.table(self._table_name)
            .delete()
            .eq("user_id", self._user_id)
            .eq("notebook_id", notebook_id)
            .execute()
        )

        return bool(response.data)

    def _to_row(self, notebook: Notebook) -> dict[str, Any]:
        return {
            "user_id": self._user_id,
            "notebook_id": notebook.notebook_id,
            "notebook_name": notebook.notebook_name,
            "notebook_url": notebook.notebook_url,
            "external_notebook_id": notebook.external_notebook_id,
            "status": notebook.status.value,
            "metadata": notebook.metadata or {},
            "created_at": (
                notebook.created_at.isoformat()
                if notebook.created_at
                else None
            ),
            "updated_at": (
                notebook.updated_at.isoformat()
                if notebook.updated_at
                else None
            ),
        }

    @classmethod
    def _from_row(cls, row: dict[str, Any]) -> Notebook:
        return Notebook(
            notebook_id=str(row["notebook_id"]),
            notebook_name=str(row["notebook_name"]),
            notebook_url=row.get("notebook_url"),
            external_notebook_id=row.get("external_notebook_id"),
            status=NotebookStatus(str(row["status"])),
            metadata=row.get("metadata") or {},
            created_at=cls._parse_datetime(
                row.get("created_at")
            ),
            updated_at=cls._parse_datetime(
                row.get("updated_at")
            ),
        )

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

    @staticmethod
    def _required_text(value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must not be empty")

        return value.strip()


class SupabaseNotebookSourceRepository:
    """User-scoped repository for NotebookSource records."""

    def __init__(
        self,
        client: Any,
        user_id: str,
        table_name: str = "notebooklm_sources",
    ) -> None:
        self._client = client
        self._user_id = self._required_text(user_id, "user_id")
        self._table_name = self._required_text(
            table_name,
            "table_name",
        )

    def save(self, source: NotebookSource) -> NotebookSource:
        response = (
            self._client.table(self._table_name)
            .upsert(
                self._to_row(source),
                on_conflict="user_id,source_id",
            )
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Supabase notebook source save returned no data"
            )

        return self._from_row(response.data[0])

    def get(self, source_id: str) -> NotebookSource | None:
        response = (
            self._client.table(self._table_name)
            .select("*")
            .eq("user_id", self._user_id)
            .eq("source_id", source_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return self._from_row(response.data[0])

    def list_for_notebook(
        self,
        notebook_id: str,
    ) -> tuple[NotebookSource, ...]:
        response = (
            self._client.table(self._table_name)
            .select("*")
            .eq("user_id", self._user_id)
            .eq("notebook_id", notebook_id)
            .order("created_at", desc=True)
            .execute()
        )

        return tuple(
            self._from_row(row)
            for row in (response.data or [])
        )

    def get_by_document(
        self,
        notebook_id: str,
        document_id: str,
    ) -> NotebookSource | None:
        response = (
            self._client.table(self._table_name)
            .select("*")
            .eq("user_id", self._user_id)
            .eq("notebook_id", notebook_id)
            .eq("document_id", document_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return self._from_row(response.data[0])

    def delete(self, source_id: str) -> bool:
        response = (
            self._client.table(self._table_name)
            .delete()
            .eq("user_id", self._user_id)
            .eq("source_id", source_id)
            .execute()
        )

        return bool(response.data)

    def _to_row(self, source: NotebookSource) -> dict[str, Any]:
        return {
            "user_id": self._user_id,
            "source_id": source.source_id,
            "notebook_id": source.notebook_id,
            "document_id": source.document_id,
            "status": source.status.value,
            "external_source_id": source.external_source_id,
            "last_synced_at": (
                source.last_synced_at.isoformat()
                if source.last_synced_at
                else None
            ),
            "last_error": source.last_error,
            "created_at": (
                source.created_at.isoformat()
                if source.created_at
                else None
            ),
            "updated_at": (
                source.updated_at.isoformat()
                if source.updated_at
                else None
            ),
        }

    @classmethod
    def _from_row(
        cls,
        row: dict[str, Any],
    ) -> NotebookSource:
        return NotebookSource(
            source_id=str(row["source_id"]),
            notebook_id=str(row["notebook_id"]),
            document_id=str(row["document_id"]),
            status=NotebookSourceStatus(str(row["status"])),
            external_source_id=row.get("external_source_id"),
            last_synced_at=cls._parse_datetime(
                row.get("last_synced_at")
            ),
            last_error=row.get("last_error"),
            created_at=cls._parse_datetime(
                row.get("created_at")
            ),
            updated_at=cls._parse_datetime(
                row.get("updated_at")
            ),
        )

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

    @staticmethod
    def _required_text(value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must not be empty")

        return value.strip()


class SupabaseSyncRunRepository:
    """User-scoped repository for synchronization runs."""

    def __init__(
        self,
        client: Any,
        user_id: str,
        table_name: str = "notebooklm_sync_runs",
    ) -> None:
        self._client = client
        self._user_id = self._required_text(user_id, "user_id")
        self._table_name = self._required_text(
            table_name,
            "table_name",
        )

    def save(self, run: SyncRun) -> SyncRun:
        response = (
            self._client.table(self._table_name)
            .upsert(
                self._to_row(run),
                on_conflict="user_id,sync_run_id",
            )
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Supabase sync run save returned no data"
            )

        return self._from_row(response.data[0])

    def get(self, sync_run_id: str) -> SyncRun | None:
        response = (
            self._client.table(self._table_name)
            .select("*")
            .eq("user_id", self._user_id)
            .eq("sync_run_id", sync_run_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return self._from_row(response.data[0])

    def list_for_notebook(
        self,
        notebook_id: str,
    ) -> tuple[SyncRun, ...]:
        response = (
            self._client.table(self._table_name)
            .select("*")
            .eq("user_id", self._user_id)
            .eq("notebook_id", notebook_id)
            .order("started_at", desc=True)
            .execute()
        )

        return tuple(
            self._from_row(row)
            for row in (response.data or [])
        )

    def _to_row(self, run: SyncRun) -> dict[str, Any]:
        return {
            "user_id": self._user_id,
            "sync_run_id": run.sync_run_id,
            "notebook_id": run.notebook_id,
            "status": run.status.value,
            "started_at": run.started_at.isoformat(),
            "finished_at": (
                run.finished_at.isoformat()
                if run.finished_at
                else None
            ),
            "source_count": run.source_count,
            "success_count": run.success_count,
            "failure_count": run.failure_count,
            "error_message": run.error_message,
            "created_at": run.started_at.isoformat(),
        }

    @classmethod
    def _from_row(cls, row: dict[str, Any]) -> SyncRun:
        started_at = cls._parse_datetime(row.get("started_at"))

        if started_at is None:
            raise ValueError(
                "Supabase sync run row is missing started_at"
            )

        return SyncRun(
            sync_run_id=str(row["sync_run_id"]),
            notebook_id=str(row["notebook_id"]),
            status=SyncRunStatus(str(row["status"])),
            started_at=started_at,
            finished_at=cls._parse_datetime(
                row.get("finished_at")
            ),
            source_count=int(row.get("source_count", 0)),
            success_count=int(row.get("success_count", 0)),
            failure_count=int(row.get("failure_count", 0)),
            error_message=row.get("error_message"),
        )

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

    @staticmethod
    def _required_text(value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must not be empty")

        return value.strip()