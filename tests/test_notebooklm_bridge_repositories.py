from __future__ import annotations

from datetime import datetime, timezone

from notebooklm_bridge.adapters.supabase_repository import (
    SupabaseNotebookRepository,
    SupabaseNotebookSourceRepository,
    SupabaseSyncRunRepository,
)
from notebooklm_bridge.models import (
    Notebook,
    NotebookSource,
    NotebookSourceStatus,
    NotebookStatus,
    SyncRun,
    SyncRunStatus,
)


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.filters = []
        self.order_field = None
        self.order_desc = False
        self.limit_count = None
        self.operation = "select"
        self.payload = None

    def select(self, *_args):
        self.operation = "select"
        return self

    def upsert(self, payload, **_kwargs):
        self.operation = "upsert"
        self.payload = payload
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def order(self, field, desc=False):
        self.order_field = field
        self.order_desc = desc
        return self

    def limit(self, count):
        self.limit_count = count
        return self

    def execute(self):
        rows = self.client.tables.setdefault(self.table_name, [])

        if self.operation == "upsert":
            key_fields = {
                "notebooklm_notebooks": (
                    "user_id",
                    "notebook_id",
                ),
                "notebooklm_sources": (
                    "user_id",
                    "source_id",
                ),
                "notebooklm_sync_runs": (
                    "user_id",
                    "sync_run_id",
                ),
            }[self.table_name]

            existing = None
            for row in rows:
                if all(
                    row.get(field) == self.payload.get(field)
                    for field in key_fields
                ):
                    existing = row
                    break

            if existing is None:
                rows.append(dict(self.payload))
                result = dict(self.payload)
            else:
                existing.update(self.payload)
                result = dict(existing)

            return FakeResponse([result])

        filtered = [
            row
            for row in rows
            if all(row.get(field) == value for field, value in self.filters)
        ]

        if self.order_field:
            filtered.sort(
                key=lambda row: row.get(self.order_field) or "",
                reverse=self.order_desc,
            )

        if self.limit_count is not None:
            filtered = filtered[: self.limit_count]

        if self.operation == "delete":
            for row in list(filtered):
                rows.remove(row)
            return FakeResponse(filtered)

        return FakeResponse(filtered)


class FakeSupabaseClient:
    def __init__(self):
        self.tables = {}

    def table(self, table_name):
        return FakeQuery(self, table_name)


def test_notebook_repository():
    client = FakeSupabaseClient()
    repo = SupabaseNotebookRepository(client, "user-1")

    notebook = Notebook(
        notebook_id="notebook-1",
        notebook_name="Toán 8 - Hình học",
        status=NotebookStatus.ACTIVE,
        metadata={"grade": 8},
    )

    saved = repo.save(notebook)

    assert saved.notebook_id == "notebook-1"
    assert saved.notebook_name == "Toán 8 - Hình học"

    loaded = repo.get("notebook-1")
    assert loaded is not None
    assert loaded.notebook_name == "Toán 8 - Hình học"

    notebooks = repo.list_all()
    assert len(notebooks) == 1

    assert repo.delete("notebook-1") is True
    assert repo.get("notebook-1") is None


def test_notebook_source_repository():
    client = FakeSupabaseClient()
    repo = SupabaseNotebookSourceRepository(client, "user-1")

    source = NotebookSource(
        source_id="source-1",
        notebook_id="notebook-1",
        document_id="document-1",
        status=NotebookSourceStatus.PENDING,
    )

    saved = repo.save(source)

    assert saved.source_id == "source-1"

    loaded = repo.get("source-1")
    assert loaded is not None
    assert loaded.document_id == "document-1"

    found = repo.get_by_document(
        "notebook-1",
        "document-1",
    )
    assert found is not None
    assert found.source_id == "source-1"

    sources = repo.list_for_notebook("notebook-1")
    assert len(sources) == 1

    assert repo.delete("source-1") is True
    assert repo.get("source-1") is None


def test_sync_run_repository():
    client = FakeSupabaseClient()
    repo = SupabaseSyncRunRepository(client, "user-1")

    started_at = datetime.now(timezone.utc)

    run = SyncRun(
        sync_run_id="run-1",
        notebook_id="notebook-1",
        status=SyncRunStatus.RUNNING,
        started_at=started_at,
        source_count=2,
        success_count=0,
        failure_count=0,
    )

    saved = repo.save(run)

    assert saved.sync_run_id == "run-1"
    assert saved.status == SyncRunStatus.RUNNING

    loaded = repo.get("run-1")
    assert loaded is not None
    assert loaded.notebook_id == "notebook-1"
    assert loaded.source_count == 2

    runs = repo.list_for_notebook("notebook-1")
    assert len(runs) == 1
    assert runs[0].sync_run_id == "run-1"


def main():
    test_notebook_repository()
    test_notebook_source_repository()
    test_sync_run_repository()
    print("NOTEBOOKLM_REPOSITORY_TESTS_OK")


if __name__ == "__main__":
    main()