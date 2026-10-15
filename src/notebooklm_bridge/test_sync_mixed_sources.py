from unittest import TestCase, main

from notebooklm_bridge.models import (
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


class MixedResultAdapter:
    def __init__(self, failing_document_id):
        self.failing_document_id = failing_document_id
        self.calls = []

    def sync_source(self, *, notebook_id, document_id):
        self.calls.append((notebook_id, document_id))

        if document_id == self.failing_document_id:
            raise RuntimeError(
                "Fake failure for selected document"
            )

        return f"fake-source-{document_id}"


class NotebookSynchronizerMixedSourcesTest(TestCase):
    def test_mixed_success_and_failure_sources(self):
        notebook_repo = InMemoryNotebookRepository()
        source_repo = InMemoryNotebookSourceRepository()
        run_repo = InMemorySyncRunRepository()

        notebook_service = NotebookService(notebook_repo)
        source_service = NotebookSourceService(source_repo)
        run_service = SyncRunService(run_repo)

        notebook = notebook_service.create(
            notebook_name="Notebook nhiều nguồn",
        )

        source_a = source_service.attach(
            notebook_id=notebook.notebook_id,
            document_id="document-A",
        )

        source_b = source_service.attach(
            notebook_id=notebook.notebook_id,
            document_id="document-B",
        )

        source_c = source_service.attach(
            notebook_id=notebook.notebook_id,
            document_id="document-C",
        )

        adapter = MixedResultAdapter(
            failing_document_id="document-B",
        )

        synchronizer = NotebookSynchronizer(
            source_service=source_service,
            run_service=run_service,
            adapter=adapter,
        )

        result = synchronizer.synchronize(
            notebook.notebook_id
        )

        self.assertEqual(len(adapter.calls), 3)

        self.assertEqual(
            result.sync_run.status,
            SyncRunStatus.FAILED,
        )
        self.assertEqual(result.sync_run.source_count, 3)
        self.assertEqual(result.sync_run.success_count, 2)
        self.assertEqual(result.sync_run.failure_count, 1)

        self.assertEqual(len(result.sources), 3)

        source_states = {
            source.document_id: source.status
            for source in result.sources
        }

        self.assertEqual(
            source_states["document-A"],
            NotebookSourceStatus.SYNCED,
        )
        self.assertEqual(
            source_states["document-B"],
            NotebookSourceStatus.FAILED,
        )
        self.assertEqual(
            source_states["document-C"],
            NotebookSourceStatus.SYNCED,
        )

        persisted_a = source_repo.get(source_a.source_id)
        persisted_b = source_repo.get(source_b.source_id)
        persisted_c = source_repo.get(source_c.source_id)

        self.assertEqual(
            persisted_a.status,
            NotebookSourceStatus.SYNCED,
        )
        self.assertEqual(
            persisted_b.status,
            NotebookSourceStatus.FAILED,
        )
        self.assertEqual(
            persisted_c.status,
            NotebookSourceStatus.SYNCED,
        )

        self.assertEqual(
            persisted_a.external_source_id,
            "fake-source-document-A",
        )
        self.assertEqual(
            persisted_c.external_source_id,
            "fake-source-document-C",
        )

        self.assertIn(
            "Fake failure for selected document",
            persisted_b.last_error,
        )

        runs = run_repo.list_for_notebook(
            notebook.notebook_id
        )

        self.assertEqual(len(runs), 1)
        self.assertEqual(
            runs[0].status,
            SyncRunStatus.FAILED,
        )
        self.assertEqual(runs[0].success_count, 2)
        self.assertEqual(runs[0].failure_count, 1)


if __name__ == "__main__":
    main()
