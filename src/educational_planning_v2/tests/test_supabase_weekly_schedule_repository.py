from dataclasses import dataclass
from pathlib import Path

from educational_planning_v2.adapters import SupabaseWeeklyScheduleRepository, WeeklyScheduleExcelAdapter
from educational_planning_v2.services import WeeklyTeachingScheduleService


TEMPLATE = Path(__file__).resolve().parents[3] / "templates/weekly_schedule/mau_du_lieu_lich_bao_giang_v2.xlsx"


@dataclass
class Response:
    data: list


class FakeQuery:
    def __init__(self, client):
        self.client = client
        self.operation = None
        self.value = None
        self.filters = []

    def upsert(self, value, on_conflict):
        assert on_conflict == "user_id,schedule_id"
        self.operation, self.value = "upsert", value
        return self

    def select(self, value):
        self.operation, self.value = "select", value
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
            key = (self.value["user_id"], self.value["schedule_id"])
            self.client.rows[key] = dict(self.value)
            return Response([dict(self.value)])
        rows = list(self.client.rows.values())
        for column, value in self.filters:
            rows = [row for row in rows if row[column] == value]
        if self.value == "schedule_data":
            rows = [{"schedule_data": row["schedule_data"]} for row in rows]
        return Response(rows)


class FakeClient:
    def __init__(self):
        self.rows = {}

    def table(self, name):
        assert name == "weekly_teaching_schedules"
        return FakeQuery(self)


def _schedule():
    data = WeeklyScheduleExcelAdapter().load(TEMPLATE)
    return WeeklyTeachingScheduleService().build(
        schedule_id="GV001-2026-2027-W05", teacher_id="GV001",
        academic_week=data.week(5, "2026-2027"), timetable_slots=data.timetable_slots,
        curriculum_periods=data.curriculum_periods, execution_records=data.execution_records,
    )


def test_save_get_and_list_round_trip():
    client = FakeClient()
    repository = SupabaseWeeklyScheduleRepository(client, "user-1")
    schedule = _schedule()

    summary = repository.save(schedule)
    assert summary.entry_count == 3
    assert repository.get(schedule.schedule_id) == schedule
    assert repository.list_for_teacher("GV001")[0].week_number == 5


def test_accounts_with_same_schedule_id_are_isolated():
    client = FakeClient()
    schedule = _schedule()
    first = SupabaseWeeklyScheduleRepository(client, "user-1")
    second = SupabaseWeeklyScheduleRepository(client, "user-2")
    first.save(schedule)

    assert second.get(schedule.schedule_id) is None
    assert second.list_for_teacher("GV001") == ()


def test_upsert_updates_same_user_schedule_instead_of_duplicating():
    client = FakeClient()
    repository = SupabaseWeeklyScheduleRepository(client, "user-1")
    repository.save(_schedule())
    repository.save(_schedule())
    assert len(client.rows) == 1


def test_migration_enables_rls_and_owner_policies():
    migration = TEMPLATE.parents[2] / "supabase/migrations/202608140001_weekly_teaching_schedules.sql"
    sql = migration.read_text(encoding="utf-8").lower()
    assert "enable row level security" in sql
    assert "to authenticated" in sql
    assert "auth.uid()" in sql
    assert "with check" in sql
    assert "grant" in sql
    assert "service_role" not in sql
