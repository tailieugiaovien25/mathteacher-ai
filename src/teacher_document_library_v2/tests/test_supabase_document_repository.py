from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from teacher_document_library_v2 import DocumentCategory, TeacherDocument, TeacherDocumentCatalog
from teacher_document_library_v2.adapters import SupabaseTeacherDocumentRepository


@dataclass
class Response:
    data: list


class FakeQuery:
    def __init__(self, client):
        self.client = client
        self.operation = None
        self.row = None
        self.filters = []

    def upsert(self, row, on_conflict):
        assert on_conflict == "user_id,document_id"
        self.operation, self.row = "upsert", row
        return self

    def select(self, columns):
        self.operation = "select"
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def limit(self, value):
        return self

    def order(self, column, desc=False):
        return self

    def execute(self):
        if self.operation == "upsert":
            key = (self.row["user_id"], self.row["document_id"])
            self.client.rows[key] = dict(self.row)
            return Response([dict(self.row)])
        rows = list(self.client.rows.values())
        for column, value in self.filters:
            rows = [row for row in rows if row[column] == value]
        if self.operation == "delete":
            for row in rows:
                self.client.rows.pop((row["user_id"], row["document_id"]), None)
        return Response(rows)


class FakeClient:
    def __init__(self):
        self.rows = {}

    def table(self, name):
        assert name == "teacher_documents"
        return FakeQuery(self)


def _document(document_id=None, title="Giáo án số 1"):
    return TeacherDocument(
        document_id=document_id or str(uuid4()), title=title,
        category=DocumentCategory.LESSON_PLAN, academic_year="2026-2027",
        subject="Toán", grade_level="6", class_name="6A1",
        file_name="giao-an.docx", mime_type="application/docx", size_bytes=0,
        storage_provider="google_drive_manual", storage_file_id="drive-1",
    )


def test_save_get_list_update_and_delete_round_trip():
    repository = SupabaseTeacherDocumentRepository(FakeClient(), "user-1")
    catalog = TeacherDocumentCatalog(repository)
    original = catalog.save(_document())
    catalog.save(_document(original.document_id, "Giáo án đã sửa"))

    assert repository.get(original.document_id).title == "Giáo án đã sửa"
    assert len(repository.list_all()) == 1
    assert repository.delete(original.document_id) is True
    assert repository.get(original.document_id) is None


def test_authenticated_accounts_are_isolated():
    client = FakeClient()
    first = SupabaseTeacherDocumentRepository(client, "user-1")
    second = SupabaseTeacherDocumentRepository(client, "user-2")
    document = TeacherDocumentCatalog(first).save(_document())
    assert second.get(document.document_id) is None
    assert second.list_all() == ()


def test_migration_enables_owner_only_rls():
    root = Path(__file__).resolve().parents[3]
    sql = (root / "supabase/migrations/202608150002_teacher_documents.sql").read_text(encoding="utf-8").lower()
    assert "enable row level security" in sql
    assert "to authenticated" in sql
    assert "auth.uid()" in sql
    assert "with check" in sql
    assert "service_role" not in sql
