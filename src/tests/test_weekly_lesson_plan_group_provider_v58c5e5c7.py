from datetime import date
from types import SimpleNamespace
import pytest
import lesson_planning_v2.services.weekly_lesson_plan_group_provider as m
from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroupingMode
from lesson_planning_v2.services.weekly_lesson_plan_group_provider import WeeklyLessonPlanGroupProvider, WeeklyLessonPlanGroupProviderError

def e(class_id="8A1", subject="ENG", period=3, lesson="U1"):
    return SimpleNamespace(class_id=class_id, subject_ref=subject, component_ref="", curriculum_period=period,
        lesson_id=lesson, lesson_title="Unit", teaching_date=date(2026,9,8), timetable_period=2,
        teaching_equipment=("TV",))

def sched(*entries):
    return SimpleNamespace(schedule_id="SYSTEM-user-1-2026-2027-W1", teacher_id="user-1",
        academic_week=SimpleNamespace(academic_year="2026-2027", week_number=1), entries=tuple(entries))

class WR:
    value=None
    def __init__(self, client, user_id): assert user_id=="user-1"
    def get(self, schedule_id): assert schedule_id=="SYSTEM-user-1-2026-2027-W1"; return self.value
class CR:
    def __init__(self, *, client): pass
    def get(self, *, class_id):
        x={"8A1":"8","8A2":"8","9A1":"9"}.get(class_id)
        return None if x is None else SimpleNamespace(grade_level=x)
class PR:
    configs=()
    def __init__(self, *, client): pass
    def list_configs(self): return self.configs
def cfg(mode, subject="ENG"):
    return SimpleNamespace(subject_ref=subject, component_ref="", mode=mode, active=True)

@pytest.fixture(autouse=True)
def repos(monkeypatch):
    monkeypatch.setattr(m,"SupabaseWeeklyScheduleRepository",WR)
    monkeypatch.setattr(m,"SupabaseClassCatalogRepository",CR)
    monkeypatch.setattr(m,"SupabaseLessonPlanGroupingPolicyRepository",PR)

def p(): return WeeklyLessonPlanGroupProvider(client=object(),user_id="user-1")

def test_by_week_keeps_occurrences_and_grade_partition():
    WR.value=sched(e("8A1",period=3),e("8A2",period=4,lesson="U2"),e("9A1",period=3))
    PR.configs=(cfg(LessonPlanGroupingMode.BY_WEEK),)
    groups=p().provide(academic_year="2026-2027",week_number=1)
    assert sorted(g.grade for g in groups)==[8,9]
    g8=[g for g in groups if g.grade==8][0]
    assert g8.curriculum_periods==(3,4)
    assert tuple(x.class_id for x in g8.occurrences)==("8A1","8A2")

def test_missing_lbg_fails_closed():
    WR.value=None; PR.configs=(cfg(LessonPlanGroupingMode.BY_WEEK),)
    with pytest.raises(WeeklyLessonPlanGroupProviderError,match="CURRENT_LBG_NOT_FOUND"):
        p().provide(academic_year="2026-2027",week_number=1)

def test_missing_policy_fails_closed():
    WR.value=sched(e()); PR.configs=()
    with pytest.raises(WeeklyLessonPlanGroupProviderError,match="ACTIVE_GROUPING_POLICY_REQUIRED"):
        p().provide(academic_year="2026-2027",week_number=1)

def test_unmatched_policy_does_not_fallback_to_by_period():
    WR.value=sched(e(subject="MATH")); PR.configs=(cfg(LessonPlanGroupingMode.BY_WEEK),)
    with pytest.raises(WeeklyLessonPlanGroupProviderError,match="AUTHORITATIVE_GROUPING_POLICY_REQUIRED"):
        p().provide(academic_year="2026-2027",week_number=1)

def test_missing_class_catalog_fails_closed():
    WR.value=sched(e("UNKNOWN")); PR.configs=(cfg(LessonPlanGroupingMode.BY_WEEK),)
    with pytest.raises(WeeklyLessonPlanGroupProviderError,match="CLASS_CATALOG_ENTRY_REQUIRED"):
        p().provide(academic_year="2026-2027",week_number=1)

def test_provider_is_read_only_and_not_shadow_authority():
    from pathlib import Path
    s=Path(m.__file__).read_text(encoding="utf-8-sig")
    assert "SystemWeeklyScheduleRuntime" not in s
    assert ".save(" not in s
    assert "_v58_c5b2_shadow_lesson_plan_groups" not in s
