"""Provider-neutral synchronization orchestration for NotebookLM sources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from notebooklm_bridge.models import NotebookSource, SyncRun
from notebooklm_bridge.service import NotebookSourceService, SyncRunService


class NotebookSourceAdapter(Protocol):
    """External provider boundary.

    The adapter may later be implemented for a supported NotebookLM
    integration mechanism without changing synchronization logic.
    """

    def sync_source(
        self,
        *,
        notebook_id: str,
        document_id: str,
    ) -> str | None: ...


@dataclass(frozen=True)
class SyncResult:
    sync_run: SyncRun
    sources: tuple[NotebookSource, ...]


class NotebookSynchronizer:
    """Synchronize mapped teacher documents through an external adapter."""

    def __init__(
        self,
        *,
        source_service: NotebookSourceService,
        run_service: SyncRunService,
        adapter: NotebookSourceAdapter,
    ) -> None:
        self._source_service = source_service
        self._run_service = run_service
        self._adapter = adapter

    def synchronize(self, notebook_id: str) -> SyncResult:
        sources = self._source_service.list_for_notebook(notebook_id)
        run = self._run_service.start(notebook_id)

        success_count = 0
        failure_count = 0
        updated_sources: list[NotebookSource] = []

        try:
            for source in sources:
                try:
                    external_source_id = self._adapter.sync_source(
                        notebook_id=source.notebook_id,
                        document_id=source.document_id,
                    )
                    updated = self._source_service.mark_synced(
                        source.source_id,
                        external_source_id=external_source_id,
                    )
                    success_count += 1
                except Exception as error:
                    updated = self._source_service.mark_failed(
                        source.source_id,
                        str(error),
                    )
                    failure_count += 1

                updated_sources.append(updated)

            completed_run = self._run_service.complete(
                run,
                source_count=len(sources),
                success_count=success_count,
                failure_count=failure_count,
            )

            return SyncResult(
                sync_run=completed_run,
                sources=tuple(updated_sources),
            )

        except Exception as error:
            failed_run = self._run_service.fail(
                run,
                str(error),
            )
            return SyncResult(
                sync_run=failed_run,
                sources=tuple(updated_sources),
            )