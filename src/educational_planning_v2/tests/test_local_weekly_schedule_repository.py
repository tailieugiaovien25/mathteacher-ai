from dataclasses import replace
from pathlib import Path

import pytest

from educational_planning_v2.adapters import LocalWeeklyScheduleRepository, WeeklyScheduleExcelAdapter
from educational_planning_v2.services import WeeklyTeachingScheduleService


TEMPLATE = Path(__file__).resolve().parents[3] / "templates/weekly_schedule/mau_du_lieu_lich_bao_giang_v2.xlsx"


@pytest.fixture
def schedule():
    data = WeeklyScheduleExcelAdapter().load(TEMPLATE)
    return WeeklyTeachingScheduleService().build(
        schedule_id="GV001-2026-2027-W05", teacher_id="GV001",
        academic_week=data.week(5, "2026-2027"), timetable_slots=data.timetable_slots,
        curriculum_periods=data.curriculum_periods, execution_records=data.execution_records,
    )


def test_save_and_get_round_trip(tmp_path, schedule):
    repository = LocalWeeklyScheduleRepository(tmp_path)
    summary = repository.save(schedule)
    assert summary.entry_count == 3
    assert repository.get(schedule.schedule_id) == schedule


def test_saving_same_identity_updates_instead_of_duplicating(tmp_path, schedule):
    repository = LocalWeeklyScheduleRepository(tmp_path)
    repository.save(schedule)
    changed = replace(schedule, entries=schedule.entries[:1])
    repository.save(changed)
    assert repository.get(schedule.schedule_id) == changed
    assert len(tuple(tmp_path.glob("*.json"))) == 1


def test_lists_only_requested_teacher(tmp_path, schedule):
    repository = LocalWeeklyScheduleRepository(tmp_path)
    repository.save(schedule)
    repository.save(replace(schedule, schedule_id="GV002-2026-2027-W05", teacher_id="GV002"))
    saved = repository.list_for_teacher("GV001")
    assert len(saved) == 1
    assert saved[0].week_number == 5


@pytest.mark.parametrize("unsafe_id", ("../secret", "a/b", "a\\b", ""))
def test_rejects_unsafe_schedule_id(tmp_path, unsafe_id):
    with pytest.raises(ValueError):
        LocalWeeklyScheduleRepository(tmp_path).get(unsafe_id)


def test_missing_schedule_returns_none(tmp_path):
    assert LocalWeeklyScheduleRepository(tmp_path).get("missing") is None
