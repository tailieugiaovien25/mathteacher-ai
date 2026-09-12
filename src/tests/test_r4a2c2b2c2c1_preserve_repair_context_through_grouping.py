from datetime import date
from types import SimpleNamespace

from educational_planning_v2.models import TeachingSession
from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroupingMode
from lesson_planning_v2.services import weekly_lesson_plan_group_provider as provider_module
from lesson_planning_v2.services.weekly_lesson_plan_group_provider import (
    WeeklyLessonPlanGroupProvider,
)
from document_standardization.lesson_plan_canonical_field_repair_runtime import (
    build_repair_scheduled_context,
)


def _provide_one_group(monkeypatch):
    teacher_id = "teacher-1"
    year = "2026-2027"
    week = 4

    entry = SimpleNamespace(
        subject_ref="FOREIGN_LANGUAGE_1",
        component_ref="",
        class_id="class-7a1",
        curriculum_period=4,
        lesson_id="lesson-4",
        lesson_title="UNIT 1: HOBBIES - Lesson 3: A CLOSER LOOK -2",
        teaching_date=date(2026, 9, 12),
        timetable_period=2,
        teaching_equipment=(),
        session=TeachingSession.MORNING,
        period_in_lesson=1,
    )

    schedule = SimpleNamespace(
        schedule_id=f"SYSTEM-{teacher_id}-{year}-W{week}",
        teacher_id=teacher_id,
        academic_week=SimpleNamespace(
            academic_year=year,
            week_number=week,
        ),
        entries=(entry,),
    )

    class FakeScheduleRepository:
        def __init__(self, client, user_id):
            self.client = client
            self.user_id = user_id

        def get(self, schedule_id):
            assert schedule_id == schedule.schedule_id
            return schedule

    class FakePolicyRepository:
        def __init__(self, client):
            self.client = client

        def list_configs(self):
            return (
                SimpleNamespace(
                    subject_ref="FOREIGN_LANGUAGE_1",
                    component_ref="",
                    mode=LessonPlanGroupingMode.BY_PERIOD,
                    active=True,
                ),
            )

    class FakeClassRepository:
        def __init__(self, client):
            self.client = client

        def get(self, class_id):
            assert class_id == "class-7a1"
            return SimpleNamespace(grade_level=7)

    monkeypatch.setattr(
        provider_module,
        "SupabaseWeeklyScheduleRepository",
        FakeScheduleRepository,
    )
    monkeypatch.setattr(
        provider_module,
        "SupabaseLessonPlanGroupingPolicyRepository",
        FakePolicyRepository,
    )
    monkeypatch.setattr(
        provider_module,
        "SupabaseClassCatalogRepository",
        FakeClassRepository,
    )

    groups = WeeklyLessonPlanGroupProvider(
        client=object(),
        user_id=teacher_id,
    ).provide(
        academic_year=year,
        week_number=week,
    )

    assert len(groups) == 1
    return groups[0]


def test_lbg_session_and_period_in_lesson_survive_provider_and_grouping(monkeypatch):
    group = _provide_one_group(monkeypatch)

    assert len(group.occurrences) == 1
    occurrence = group.occurrences[0]

    assert occurrence.session is TeachingSession.MORNING
    assert occurrence.period_in_lesson == 1


def test_preserved_occurrence_builds_repair_scheduled_context(monkeypatch):
    group = _provide_one_group(monkeypatch)
    occurrence = group.occurrences[0]

    payload = {
        "subject_ref": group.subject_ref,
        "component_ref": group.component_ref,
        "lesson_id": group.lesson_id,
        "lesson_title": group.lesson_title,
        "occurrences": [
            {
                "class_id": occurrence.class_id,
                "class_display": "7A1",
                "teaching_date": occurrence.teaching_date.isoformat(),
                "timetable_period": occurrence.timetable_period,
                "curriculum_period": occurrence.curriculum_period,
                "session": occurrence.session.value,
                "period_in_lesson": occurrence.period_in_lesson,
            }
        ],
    }

    context = build_repair_scheduled_context(
        payload,
        field_key="class_name",
        teacher_value="7A1",
    )

    assert context.class_id == "class-7a1"
    assert context.curriculum_period == 4
    assert context.session is TeachingSession.MORNING
    assert context.timetable_period == 2
    assert context.period_in_lesson == 1
