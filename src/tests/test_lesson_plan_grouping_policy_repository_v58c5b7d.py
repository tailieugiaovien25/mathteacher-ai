from lesson_planning_v2.adapters.supabase_lesson_plan_grouping_policy_repository import (
    SupabaseLessonPlanGroupingPolicyRepository,
)
from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroupingMode


class Query:
    def __init__(self, rows):
        self.rows = rows
    def select(self, *args, **kwargs): return self
    def eq(self, *args, **kwargs): return self
    def order(self, *args, **kwargs): return self
    def execute(self):
        class R:
            data = self.rows
        return R()


class Client:
    def __init__(self, rows):
        self.rows = rows
    def table(self, name):
        assert name == "lesson_plan_grouping_policy_config"
        return Query(self.rows)


def test_repository_reads_by_week():
    repo = SupabaseLessonPlanGroupingPolicyRepository(
        Client([{
            "subject_ref": "ENG",
            "component_ref": "",
            "grouping_mode": "BY_WEEK",
            "status": "ACTIVE",
            "rule_version": 1,
        }])
    )
    rows = repo.list_configs()
    assert rows[0].mode is LessonPlanGroupingMode.BY_WEEK
