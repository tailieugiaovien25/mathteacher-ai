from __future__ import annotations

import unittest
from datetime import datetime, timezone
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
from notebooklm_bridge.service import (
    NotebookSourceService,
    SyncRunService,
)
from notebooklm_bridge.sync import NotebookSynchronizer


class InMemoryNotebookRepository(NotebookRepository):
    def __init__(self) -> None:
        self.items: dict[str, Notebook] = {}

    def save(self, notebook: Notebook) -> Notebook:
        self.items[notebook.notebook_id] = notebook
        return notebook

    def get(self, notebook_id: str) -> Notebook | None:
        return self.items.get(notebook_id)

    def list_all(self) -> tuple[Notebook, ...]:
        return tuple(self.items.values())

    def delete(self, notebook_id: str) -> bool:
        return self.items.pop(notebook_id, None) is not None


class InMemoryNotebookSourceRepository(NotebookSourceRepository):
    def __init__(self) -> None:
        self.items: dict[str, NotebookSource] = {}

    def save(self, source: NotebookSource) -> NotebookSource:
        self.items[source.source_id] = source
        return source

    def get(self, source_id: str) -> NotebookSource | None:
        return self.items.get(source_id)

    def list_for_notebook(
        self,
        notebook_id: str,
    ) -> tuple[NotebookSource, ...]:
        return tuple(
            source
            for source in self.items.values()
            if source.notebook_id == notebook_id
        )

    def get_by_document(
        self,
        notebook_id: str,
        document_id: str,
    ) -> NotebookSource | None:
        for source in self.items.values():
            if (
                source.notebook_id == notebook_id
                and source.document_id == document_id
            ):
                return source
        return None

    def delete(self, source_id: str) -> bool:
        return self.items.pop(source_id, None) is not None


class InMemorySyncRunRepository(SyncRunRepository):
    def __init__(self) -> None:
        self.items: dict[str, SyncRun] = {}

    def save(self, run: SyncRun) -> SyncRun:
        self.items[run.sync_run_id] = run
        return run

    def get(self, sync_run_id: str) -> SyncRun | None:
        return self.items.get(sync_run_id)

    def list_for_notebook(
        self,
        notebook_id: str,
    ) -> tuple[SyncRun, ...]:
        return tuple(
            run
            for run in self.items.values()
            if run.notebook_id == notebook_id
        )


class FakeNotebookLMAdapter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def sync_source(
        self,
        *,
        notebook_id: str,
        document_id: str,
    ) -> str | None:
        self.calls.append((notebook_id, document_id))
        return f"fake-source-{document_id}"


class NotebookSynchronizerWorkflowTest(unittest.TestCase):
    def test_notebook_attach_sync_and_syncrun(self) -> None:
        notebook_repository = InMemoryNotebookRepository()
        source_repository = InMemoryNotebookSourceRepository()
        run_repository = InMemorySyncRunRepository()

        source_service = NotebookSourceService(source_repository)
        run_service = SyncRunService(run_repository)
        adapter = FakeNotebookLMAdapter()

        notebook_id = str(uuid4())
        document_id = str(uuid4())

        notebook = Notebook(
            notebook_id=notebook_id,
            notebook_name="Toán 7 - Hình học",
            status=NotebookStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
        )
        notebook_repository.save(notebook)

        source = source_service.attach(
            notebook_id=notebook_id,
            document_id=document_id,
        )

        self.assertEqual(source.notebook_id, notebook_id)
        self.assertEqual(source.document_id, document_id)
        self.assertEqual(source.status, NotebookSourceStatus.PENDING)

        synchronizer = NotebookSynchronizer(
            source_service=source_service,
            run_service=run_service,
            adapter=adapter,
        )

        result = synchronizer.synchronize(notebook_id)

        self.assertEqual(len(adapter.calls), 1)
        self.assertEqual(
            adapter.calls[0],
            (notebook_id, document_id),
        )

        self.assertEqual(result.sync_run.status, SyncRunStatus.SUCCEEDED)
        self.assertEqual(result.sync_run.source_count, 1)
        self.assertEqual(result.sync_run.success_count, 1)
        self.assertEqual(result.sync_run.failure_count, 0)
        self.assertIsNotNone(result.sync_run.finished_at)

        self.assertEqual(len(result.sources), 1)

        updated_source = result.sources[0]

        self.assertEqual(
            updated_source.status,
            NotebookSourceStatus.SYNCED,
        )
        self.assertEqual(
            updated_source.external_source_id,
            f"fake-source-{document_id}",
        )
        self.assertIsNotNone(updated_source.last_synced_at)
        self.assertIsNone(updated_source.last_error)

        stored_source = source_repository.get(source.source_id)

        self.assertIsNotNone(stored_source)
        assert stored_source is not None

        self.assertEqual(
            stored_source.status,
            NotebookSourceStatus.SYNCED,
        )

        runs = run_repository.list_for_notebook(notebook_id)

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].status, SyncRunStatus.SUCCEEDED)


if __name__ == "__main__":
    unittest.main()
