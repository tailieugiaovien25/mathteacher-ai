from dataclasses import dataclass
from pathlib import Path

from educational_planning_v2.adapters import SupabaseTeacherProfileRepository
from educational_planning_v2.models import TeacherProfile


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
        assert on_conflict == "user_id"
        self.operation, self.row = "upsert", row
        return self

    def select(self, columns):
        self.operation = "select"
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def limit(self, value):
        return self

    def execute(self):
        if self.operation == "upsert":
            self.client.rows[self.row["user_id"]] = dict(self.row)
            return Response([dict(self.row)])
        rows = list(self.client.rows.values())
        for column, value in self.filters:
            rows = [row for row in rows if row[column] == value]
        return Response(rows)


class FakeClient:
    def __init__(self):
        self.rows = {}

    def table(self, name):
        assert name == "teacher_profiles"
        return FakeQuery(self)


def _profile(name="Nguyễn Văn A"):
    return TeacherProfile(
        teacher_code="GV001", full_name=name, school_name="THCS Mẫu",
        subjects=("Toán",), grade_levels=("6", "7"),
        default_academic_year="2026-2027",
    )


def test_save_get_and_update_profile():
    client = FakeClient()
    repository = SupabaseTeacherProfileRepository(client, "user-1")
    repository.save(_profile())
    repository.save(_profile("Nguyễn Văn B"))
    assert repository.get().full_name == "Nguyễn Văn B"
    assert len(client.rows) == 1


def test_profiles_are_isolated_by_authenticated_account():
    client = FakeClient()
    first = SupabaseTeacherProfileRepository(client, "user-1")
    second = SupabaseTeacherProfileRepository(client, "user-2")
    first.save(_profile())
    assert second.get() is None


def test_migration_enables_owner_only_rls():
    root = Path(__file__).resolve().parents[3]
    sql = (root / "supabase/migrations/202608150001_teacher_profiles.sql").read_text(encoding="utf-8").lower()
    assert "enable row level security" in sql
    assert "to authenticated" in sql
    assert "auth.uid()" in sql
    assert "with check" in sql
    assert "service_role" not in sql
