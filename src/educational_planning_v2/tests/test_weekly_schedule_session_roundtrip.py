from datetime import date

from educational_planning_v2.adapters.local_weekly_schedule_repository import (
    LocalWeeklyScheduleRepository,
)
from educational_planning_v2.adapters.weekly_schedule_codec import (
    schedule_from_dict,
    schedule_to_dict,
)
from educational_planning_v2.models import (
    AcademicWeek,
    TeachingSession,
    WeeklyTeachingSchedule,
    WeeklyTeachingScheduleEntry,
)


def _schedule(
    session: TeachingSession,
) -> WeeklyTeachingSchedule:
    return WeeklyTeachingSchedule(
        schedule_id="GV001-2026-2027-W05-SESSION",
        teacher_id="GV001",
        academic_week=AcademicWeek(
            academic_year="2026-2027",
            week_number=5,
            start_date=date(2026, 10, 5),
            end_date=date(2026, 10, 11),
        ),
        entries=(
            WeeklyTeachingScheduleEntry(
                teaching_date=date(2026, 10, 5),
                weekday=1,
                timetable_period=1,
                session=session,
                teacher_id="GV001",
                class_id="8A",
                subject_ref="MATH",
                component_ref="ALGEBRA",
                curriculum_period=1,
                lesson_id="LESSON-001",
                lesson_title="Lesson 1",
                period_in_lesson=1,
                total_lesson_periods=1,
                teaching_equipment=(),
            ),
        ),
    )


def test_codec_preserves_afternoon_session():
    schedule = _schedule(
        TeachingSession.AFTERNOON
    )

    payload = schedule_to_dict(
        schedule
    )

    assert (
        payload["entries"][0]["session"]
        == "AFTERNOON"
    )

    restored = schedule_from_dict(
        payload
    )

    assert (
        restored.entries[0].session
        is TeachingSession.AFTERNOON
    )


def test_codec_loads_legacy_payload_as_morning():
    schedule = _schedule(
        TeachingSession.AFTERNOON
    )

    payload = schedule_to_dict(
        schedule
    )

    payload["entries"][0].pop(
        "session"
    )

    restored = schedule_from_dict(
        payload
    )

    assert (
        restored.entries[0].session
        is TeachingSession.MORNING
    )


def test_local_repository_preserves_afternoon_session(
    tmp_path,
):
    schedule = _schedule(
        TeachingSession.AFTERNOON
    )

    repository = (
        LocalWeeklyScheduleRepository(
            tmp_path
        )
    )

    repository.save(
        schedule
    )

    restored = repository.get(
        schedule.schedule_id
    )

    assert restored is not None

    assert (
        restored.entries[0].session
        is TeachingSession.AFTERNOON
    )


def test_local_repository_loads_legacy_json_as_morning(
    tmp_path,
):
    schedule = _schedule(
        TeachingSession.AFTERNOON
    )

    repository = (
        LocalWeeklyScheduleRepository(
            tmp_path
        )
    )

    repository.save(
        schedule
    )

    path = (
        tmp_path
        / f"{schedule.schedule_id}.json"
    )

    import json

    payload = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    payload[
        "schedule"
    ][
        "entries"
    ][0].pop(
        "session"
    )

    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    restored = repository.get(
        schedule.schedule_id
    )

    assert restored is not None

    assert (
        restored.entries[0].session
        is TeachingSession.MORNING
    )
