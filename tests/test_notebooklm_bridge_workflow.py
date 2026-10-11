from __future__ import annotations

from datetime import datetime, timezone

from notebooklm_bridge.models import (
    Notebook,
    NotebookSource,
    NotebookSourceStatus,
    SyncRun,
    SyncRunStatus,
)
from notebooklm_bridge.service import (
    NotebookService,
    NotebookSourceService,
    SyncRunService,
)
from notebooklm_bridge.sync import NotebookSynchronizer


class InMemoryNotebookRepository:
    def __init__(self):
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


class InMemoryNotebookSourceRepository:
    def __init__(self):
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


class InMemorySyncRunRepository:
    def __init__(self):
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
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def sync_source(
        self,
        *,
        notebook_id: str,
        document_id: str,
    ) -> str | None:
        self.calls.append(
            (notebook_id, document_id)
        )
        return f"external-{document_id}"


def main():
    # 1. Khởi tạo repository giả.
    notebook_repository = InMemoryNotebookRepository()
    source_repository = InMemoryNotebookSourceRepository()
    run_repository = InMemorySyncRunRepository()

    # 2. Khởi tạo service.
    notebook_service = NotebookService(
        notebook_repository
    )
    source_service = NotebookSourceService(
        source_repository
    )
    run_service = SyncRunService(
        run_repository
    )

    # 3. Tạo Notebook.
    notebook = notebook_service.create(
        notebook_name="Toán 8 - Hình học",
        notebook_url="https://notebooklm.google.com/",
    )

    assert notebook.notebook_name == "Toán 8 - Hình học"

    # 4. Gắn tài liệu giáo viên vào Notebook.
    source = source_service.attach(
        notebook_id=notebook.notebook_id,
        document_id="document-001",
    )

    assert source.status == NotebookSourceStatus.PENDING

    # 5. Khởi tạo adapter giả.
    adapter = FakeNotebookLMAdapter()

    # 6. Khởi tạo Synchronizer.
    synchronizer = NotebookSynchronizer(
        source_service=source_service,
        run_service=run_service,
        adapter=adapter,
    )

    # 7. Chạy toàn bộ workflow.
    result = synchronizer.synchronize(
        notebook.notebook_id
    )

    # 8. Kiểm tra adapter đã được gọi.
    assert adapter.calls == [
        (
            notebook.notebook_id,
            "document-001",
        )
    ]

    # 9. Kiểm tra source đã chuyển sang SYNCED.
    assert len(result.sources) == 1

    synced_source = result.sources[0]

    assert synced_source.status == NotebookSourceStatus.SYNCED
    assert (
        synced_source.external_source_id
        == "external-document-001"
    )
    assert synced_source.last_synced_at is not None
    assert synced_source.last_error is None

    # 10. Kiểm tra SyncRun.
    sync_run = result.sync_run

    assert sync_run.status == SyncRunStatus.SUCCEEDED
    assert sync_run.source_count == 1
    assert sync_run.success_count == 1
    assert sync_run.failure_count == 0
    assert sync_run.finished_at is not None

    # 11. Kiểm tra dữ liệu thực sự được lưu lại
    # trong các repository.
    stored_source = source_repository.get(
        source.source_id
    )

    assert stored_source is not None
    assert stored_source.status == NotebookSourceStatus.SYNCED

    stored_run = run_repository.get(
        sync_run.sync_run_id
    )

    assert stored_run is not None
    assert stored_run.status == SyncRunStatus.SUCCEEDED

    print("NOTEBOOKLM_WORKFLOW_TEST_OK")


if __name__ == "__main__":
    main()