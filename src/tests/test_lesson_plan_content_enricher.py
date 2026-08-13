from intelligence.lesson_plan_builder import LessonPlanBuilder
from intelligence.lesson_plan_content_enricher import LessonPlanContentEnricher
from models.lesson_model import LessonModel
from models.math_lesson_plan_schema import create_math_lesson_plan_schema


def make_plan(requirement="Nhận biết được đối tượng học tập."):
    lesson = LessonModel(
        subject="Môn mẫu",
        grade="6",
        lesson_name="Bài học mẫu",
        learning_requirements=[requirement],
    )
    return LessonPlanBuilder().build(
        lesson=lesson,
        schema=create_math_lesson_plan_schema(),
    )


def test_enricher_fills_all_standard_activities_without_mutating_input():
    original = make_plan()
    enriched = LessonPlanContentEnricher().enrich(original)

    assert all(not activity.objective for activity in original.activities)
    assert all(activity.objective for activity in enriched.activities)
    assert all(activity.content for activity in enriched.activities)
    assert all(activity.product for activity in enriched.activities)
    assert all(activity.organization_steps for activity in enriched.activities)
    assert enriched.metadata["content_enricher"] == "rule_based_v1"


def test_enricher_uses_changed_requirement_without_changing_system_logic():
    first = LessonPlanContentEnricher().enrich(make_plan("Yêu cầu dữ liệu A"))
    second = LessonPlanContentEnricher().enrich(make_plan("Yêu cầu dữ liệu B"))

    assert "Yêu cầu dữ liệu A" in first.activities[0].objective
    assert "Yêu cầu dữ liệu B" in second.activities[0].objective
    assert [item.key for item in first.activities] == [
        item.key for item in second.activities
    ]
    assert [len(item.organization_steps) for item in first.activities] == [
        len(item.organization_steps) for item in second.activities
    ]
