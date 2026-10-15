from datetime import datetime, timezone
from unittest import TestCase, main

from notebooklm_bridge.models import (
    Notebook,
    NotebookSourceStatus,
    SyncRunStatus,
)
from notebooklm_bridge.repository import (
    NotebookRepository,
    NotebookSourceRepository,
    SyncRunRepository,
)
from notebooklm_bridge.service import (
    NotebookService,
    NotebookSourceService,
    SyncRunService,
)
from notebooklm_bridge.sync import NotebookSynchronizer


class InMemoryNotebookRepository(NotebookRepository):
    def __init__(self):
        self.items = {}

    def save(self, notebook):
        self.items[notebook.notebook_id] = notebook
        return notebook

    def get(self, notebook_id):
        return self.items.get(notebook_id)

    def list_all(self):
        return tuple(self.items.values())

    def delete(self, notebook_id):
        return self.items.pop(notebook_id, None) is not None


class InMemoryNotebookSourceRepository(NotebookSourceRepository):
    def __init__(self):
        self.items = {}

    def save(self, source):
        self.items[source.source_id] = source
        return source

    def get(self, source_id):
        return self.items.get(source_id)

    def list_for_notebook(self, notebook_id):
        return tuple(
            item for item in self.items.values()
            if item.notebook_id == notebook_id
        )

    def get_by_document(self, notebook_id, document_id):
        for item in self.items.values():
            if (
                item.notebook_id == notebook_id
                and item.document_id == document_id
            ):
                return item
        return None

    def delete(self, source_id):
        return self.items.pop(source_id, None) is not None


class InMemorySyncRunRepository(SyncRunRepository):
    def __init__(self):
        self.items = {}

    def save(self, run):
        self.items[run.sync_run_id] = run
        return run

    def get(self, sync_run_id):
        return self.items.get(sync_run_id)

    def list_for_notebook(self, notebook_id):
        return tuple(
            item for item in self.items.values()
            if item.notebook_id == notebook_id
        )


class FailingNotebookLMAdapter:
    def __init__(self):
        self.calls = []

    def sync_source(self, *, notebook_id, document_id):
        self.calls.append((notebook_id, document_id))
        raise RuntimeError("Fake NotebookLM adapter failure")


class NotebookSynchronizerFailureTest(TestCase):
    def test_adapter_failure_marks_source_and_syncrun_failed(self):
        notebook_repo = InMemoryNotebookRepository()
        source_repo = InMemoryNotebookSourceRepository()
        run_repo = InMemorySyncRunRepository()

        notebook_service = NotebookService(notebook_repo)
        source_service = NotebookSourceService(source_repo)
        run_service = SyncRunService(run_repo)

        notebook = notebook_service.create(
            notebook_name="Notebook lỗi thử nghiệm",
        )

        source = source_service.attach(
            notebook_id=notebook.notebook_id,
            document_id="document-failure-001",
        )

        adapter = FailingNotebookLMAdapter()

        synchronizer = NotebookSynchronizer(
            source_service=source_service,
            run_service=run_service,
            adapter=adapter,
        )

        result = synchronizer.synchronize(notebook.notebook_id)

        self.assertEqual(len(adapter.calls), 1)

        self.assertEqual(
            result.sync_run.status,
            SyncRunStatus.FAILED,
        )
        self.assertEqual(result.sync_run.source_count, 1)
        self.assertEqual(result.sync_run.success_count, 0)
        self.assertEqual(result.sync_run.failure_count, 1)

        self.assertEqual(len(result.sources), 1)

        updated_source = result.sources[0]

        self.assertEqual(
            updated_source.status,
            NotebookSourceStatus.FAILED,
        )
        self.assertIn(
            "Fake NotebookLM adapter failure",
            updated_source.last_error,
        )

        persisted_source = source_repo.get(source.source_id)

        self.assertEqual(
            persisted_source.status,
            NotebookSourceStatus.FAILED,
        )

        persisted_runs = run_repo.list_for_notebook(
            notebook.notebook_id
        )

        self.assertEqual(len(persisted_runs), 1)
        self.assertEqual(
            persisted_runs[0].status,
            SyncRunStatus.FAILED,
        )


if __name__ == "__main__":
    main()
