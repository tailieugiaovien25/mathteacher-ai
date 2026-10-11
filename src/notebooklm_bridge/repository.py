"""Repository contracts for the NotebookLM integration boundary."""

from __future__ import annotations

from typing import Protocol

from notebooklm_bridge.models import Notebook, NotebookSource, SyncRun


class NotebookRepository(Protocol):
    def save(self, notebook: Notebook) -> Notebook: ...

    def get(self, notebook_id: str) -> Notebook | None: ...

    def list_all(self) -> tuple[Notebook, ...]: ...

    def delete(self, notebook_id: str) -> bool: ...


class NotebookSourceRepository(Protocol):
    def save(self, source: NotebookSource) -> NotebookSource: ...

    def get(self, source_id: str) -> NotebookSource | None: ...

    def list_for_notebook(
        self,
        notebook_id: str,
    ) -> tuple[NotebookSource, ...]: ...

    def get_by_document(
        self,
        notebook_id: str,
        document_id: str,
    ) -> NotebookSource | None: ...

    def delete(self, source_id: str) -> bool: ...


class SyncRunRepository(Protocol):
    def save(self, run: SyncRun) -> SyncRun: ...

    def get(self, sync_run_id: str) -> SyncRun | None: ...

    def list_for_notebook(
        self,
        notebook_id: str,
    ) -> tuple[SyncRun, ...]: ...