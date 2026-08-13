import sys

sys.path.insert(0, "src")

from intelligence.lesson_plan_builder import (
    LessonPlanBuilder,
)
from models.lesson_model import LessonModel
from models.math_lesson_plan_schema import (
    create_math_lesson_plan_schema,
)


def main() -> None:
    lesson = LessonModel(
        subject="Toán",
        grade="8C4",
        lesson_name="Bài 2. Đa thức",
        period_count=2,
        learning_requirements=[
            "Nhận biết được khái niệm đa thức."
        ],
        registered_equipment=[
            "Máy chiếu",
            "SGK",
        ],
        learning_resources=[
            "SGK",
            "Vở ghi",
        ],
        source_file="sample.xlsm",
        source_sheet="LuuBG",
        source_row=81,
    )

    schema = create_math_lesson_plan_schema()

    builder = LessonPlanBuilder()

    lesson_plan = builder.build(
        lesson=lesson,
        schema=schema,
    )

    assert lesson_plan.subject == "Toán"
    assert lesson_plan.grade == "8C4"
    assert lesson_plan.lesson_name == "Bài 2. Đa thức"
    assert lesson_plan.total_periods == 2

    assert len(
        lesson_plan.objectives.knowledge
    ) == 1

    assert len(
        lesson_plan.resources.teacher
    ) == 2

    assert len(
        lesson_plan.activities
    ) == 4

    assert (
        lesson_plan.activities[0]
        .organization_layout
        == "single"
    )

    assert (
        lesson_plan.activities[1]
        .organization_layout
        == "two_column"
    )

    assert (
        lesson_plan.metadata["schema_id"]
        == "math_lesson_plan_v1_1"
    )

    assert (
        lesson_plan.metadata["source_row"]
        == 81
    )

    print("=" * 70)
    print("LP-02A - LESSON PLAN BUILDER TEST")
    print("=" * 70)

    print("- LessonModel input: PASS")
    print("- Schema input: PASS")
    print("- LessonPlanContent output: PASS")
    print("- Objectives mapping: PASS")
    print("- Resources mapping: PASS")
    print("- Activity creation: PASS")
    print("- Layout mapping: PASS")
    print("- Metadata traceability: PASS")

    print("\nKẾT QUẢ: 8/8 TEST PASS")


if __name__ == "__main__":
    main()