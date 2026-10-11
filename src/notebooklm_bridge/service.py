"""Business services for the NotebookLM integration boundary."""

from __future__ import annotations

from uuid import uuid4

from notebooklm_bridge.models import (
    Notebook,
    NotebookSource,
    NotebookSourceStatus,
    NotebookStatus,
    SyncRun,
    SyncRunStatus,
)
from notebooklm_bridge.repository import (
    NotebookRepository,
    NotebookSourceRepository,
    SyncRunRepository,
)


class NotebookService:
    """Manage teacher-owned NotebookLM notebook metadata."""

    def __init__(self, repository: NotebookRepository) -> None:
        self._repository = repository

    def create(
        self,
        *,
        notebook_name: str,
        notebook_url: str | None = None,
        external_notebook_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> Notebook:
        name = notebook_name.strip()
        if not name:
            raise ValueError("notebook_name must not be empty")

        notebook = Notebook(
            notebook_id=str(uuid4()),
            notebook_name=name,
            notebook_url=notebook_url,
            external_notebook_id=external_notebook_id,
            status=NotebookStatus.ACTIVE,
            metadata=metadata or {},
        )
        return self._repository.save(notebook)

    def get(self, notebook_id: str) -> Notebook | None:
        return self._repository.get(notebook_id)

    def list_all(self) -> tuple[Notebook, ...]:
        return self._repository.list_all()

    def archive(self, notebook_id: str) -> Notebook:
        notebook = self._repository.get(notebook_id)
        if notebook is None:
            raise ValueError("notebook not found")

        archived = Notebook(
            **{
                **notebook.__dict__,
                "status": NotebookStatus.ARCHIVED,
            }
        )
        return self._repository.save(archived)


class NotebookSourceService:
    """Manage mappings between teacher documents and notebooks."""

    def __init__(
        self,
        repository: NotebookSourceRepository,
    ) -> None:
        self._repository = repository

    def attach(
        self,
        *,
        notebook_id: str,
        document_id: str,
    ) -> NotebookSource:
        notebook_id = self._required_text(notebook_id, "notebook_id")
        document_id = self._required_text(document_id, "document_id")

        existing = self._repository.get_by_document(
            notebook_id,
            document_id,
        )
        if existing is not None:
            return existing

        source = NotebookSource(
            source_id=str(uuid4()),
            notebook_id=notebook_id,
            document_id=document_id,
            status=NotebookSourceStatus.PENDING,
        )
        return self._repository.save(source)

    def get(self, source_id: str) -> NotebookSource | None:
        return self._repository.get(source_id)

    def list_for_notebook(
        self,
        notebook_id: str,
    ) -> tuple[NotebookSource, ...]:
        return self._repository.list_for_notebook(
            self._required_text(notebook_id, "notebook_id")
        )

    def mark_synced(
        self,
        source_id: str,
        *,
        external_source_id: str | None = None,
    ) -> NotebookSource:
        source = self._repository.get(source_id)
        if source is None:
            raise ValueError("source not found")

        from datetime import datetime, timezone

        synced = NotebookSource(
            **{
                **source.__dict__,
                "status": NotebookSourceStatus.SYNCED,
                "external_source_id": external_source_id,
                "last_synced_at": datetime.now(timezone.utc),
                "last_error": None,
            }
        )
        return self._repository.save(synced)

    def mark_failed(
        self,
        source_id: str,
        error_message: str,
    ) -> NotebookSource:
        source = self._repository.get(source_id)
        if source is None:
            raise ValueError("source not found")

        message = str(error_message).strip()
        if not message:
            message = "Unknown synchronization error"

        failed = NotebookSource(
            **{
                **source.__dict__,
                "status": NotebookSourceStatus.FAILED,
                "last_error": message[:4000],
            }
        )
        return self._repository.save(failed)

    @staticmethod
    def _required_text(value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must not be empty")
        return value.strip()


class SyncRunService:
    """Track synchronization runs without knowing the external provider."""

    def __init__(self, repository: SyncRunRepository) -> None:
        self._repository = repository

    def start(self, notebook_id: str) -> SyncRun:
        from datetime import datetime, timezone

        notebook_id = self._required_text(notebook_id, "notebook_id")
        run = SyncRun(
            sync_run_id=str(uuid4()),
            notebook_id=notebook_id,
            status=SyncRunStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        return self._repository.save(run)

    def complete(
        self,
        run: SyncRun,
        *,
        source_count: int,
        success_count: int,
        failure_count: int,
    ) -> SyncRun:
        from datetime import datetime, timezone

        self._validate_counts(
            source_count,
            success_count,
            failure_count,
        )

        completed = SyncRun(
            **{
                **run.__dict__,
                "status": (
                    SyncRunStatus.FAILED
                    if failure_count > 0
                    else SyncRunStatus.SUCCEEDED
                ),
                "finished_at": datetime.now(timezone.utc),
                "source_count": source_count,
                "success_count": success_count,
                "failure_count": failure_count,
            }
        )
        return self._repository.save(completed)

    def fail(
        self,
        run: SyncRun,
        error_message: str,
    ) -> SyncRun:
        from datetime import datetime, timezone

        message = str(error_message).strip()
        if not message:
            message = "Unknown synchronization error"

        failed = SyncRun(
            **{
                **run.__dict__,
                "status": SyncRunStatus.FAILED,
                "finished_at": datetime.now(timezone.utc),
                "error_message": message[:4000],
            }
        )
        return self._repository.save(failed)

    @staticmethod
    def _required_text(value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must not be empty")
        return value.strip()

    @staticmethod
    def _validate_counts(
        source_count: int,
        success_count: int,
        failure_count: int,
    ) -> None:
        counts = (
            source_count,
            success_count,
            failure_count,
        )
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in counts
        ):
            raise ValueError("sync counts must be non-negative integers")

        if success_count + failure_count > source_count:
            raise ValueError(
                "success_count + failure_count must not exceed source_count"
            )