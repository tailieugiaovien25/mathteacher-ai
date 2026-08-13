import sys
from dataclasses import asdict

sys.path.insert(0, "src")

from models.lesson_plan_content import (
    LearningActivity,
    LessonObjectives,
    LessonPlanContent,
    OrganizationStep,
    TeachingResources,
)
from models.math_lesson_plan_schema import (
    create_math_lesson_plan_schema,
)


def main() -> None:
    schema = create_math_lesson_plan_schema()

    assert schema.schema_id == "math_lesson_plan_v1_1"
    assert schema.subject == "Toán"
    assert schema.version == "1.1"
    assert len(schema.sections) == 3
    assert len(schema.activities) == 4

    opening_schema = schema.activities[0]
    knowledge_schema = schema.activities[1]
    practice_schema = schema.activities[2]
    application_schema = schema.activities[3]

    assert opening_schema.default_layout == "single"

    assert knowledge_schema.default_layout == "two_column"
    assert knowledge_schema.allow_subactivities

    assert "single" in practice_schema.allowed_layouts
    assert "two_column" in practice_schema.allowed_layouts

    assert "single" in application_schema.allowed_layouts
    assert "two_column" in application_schema.allowed_layouts

    objectives = LessonObjectives(
        knowledge=[
            "Nhận biết được khái niệm đa thức."
        ],
        competencies=[
            "Phát triển năng lực tư duy và lập luận toán học."
        ],
        qualities=[
            "Chăm chỉ trong học tập."
        ],
    )

    resources = TeachingResources(
        teacher=[
            "SGK",
            "Máy chiếu",
        ],
        students=[
            "SGK",
            "Vở ghi",
        ],
    )

    opening = LearningActivity(
        key="opening",
        title="Hoạt động 1. Mở đầu",
        objective="Tạo tình huống học tập.",
        content="Khởi động bài học.",
        product="Câu trả lời ban đầu của học sinh.",
        organization_layout="single",
        organization_steps=[
            OrganizationStep(
                title="Bước 1. Giao nhiệm vụ",
                teacher_student_activity=(
                    "Giáo viên giao nhiệm vụ khởi động."
                ),
            ),
            OrganizationStep(
                title="Bước 2. Thực hiện nhiệm vụ",
                teacher_student_activity=(
                    "Học sinh thực hiện nhiệm vụ."
                ),
            ),
        ],
    )

    subactivity = LearningActivity(
        key="knowledge_formation_1",
        title="Hoạt động 2.1. Nhận biết đa thức",
        objective="Hình thành khái niệm đa thức.",
        content="Tìm hiểu ví dụ về đa thức.",
        product="Học sinh nhận biết được đa thức.",
        organization_layout="two_column",
        organization_steps=[
            OrganizationStep(
                title="Bước 1. Giao nhiệm vụ",
                teacher_student_activity=(
                    "Giáo viên giao nhiệm vụ quan sát ví dụ."
                ),
                expected_product=(
                    "Học sinh xác định được các biểu thức là đa thức."
                ),
            )
        ],
    )

    knowledge_formation = LearningActivity(
        key="knowledge_formation",
        title="Hoạt động 2. Hình thành kiến thức",
        organization_layout="two_column",
        subactivities=[
            subactivity,
        ],
    )

    lesson_plan = LessonPlanContent(
        subject="Toán",
        grade="8C4",
        lesson_name="Bài 2. Đa thức",
        total_periods=2,
        objectives=objectives,
        resources=resources,
        activities=[
            opening,
            knowledge_formation,
        ],
        metadata={
            "schema_id": schema.schema_id,
        },
    )

    assert lesson_plan.subject == "Toán"
    assert lesson_plan.grade == "8C4"
    assert lesson_plan.total_periods == 2

    assert len(lesson_plan.objectives.knowledge) == 1
    assert len(lesson_plan.resources.teacher) == 2
    assert len(lesson_plan.activities) == 2

    assert (
        lesson_plan.activities[1]
        .subactivities[0]
        .organization_layout
        == "two_column"
    )

    lesson_plan_dict = asdict(lesson_plan)

    assert lesson_plan_dict["subject"] == "Toán"
    assert lesson_plan_dict["metadata"]["schema_id"] == (
        "math_lesson_plan_v1_1"
    )

    print("=" * 70)
    print("LP-01C - LESSON PLANNING DATA MODEL TEST")
    print("=" * 70)

    print("- LessonPlanSchema: PASS")
    print("- Math schema sections: PASS")
    print("- Math activity layouts: PASS")
    print("- LessonObjectives: PASS")
    print("- TeachingResources: PASS")
    print("- LearningActivity: PASS")
    print("- Subactivities: PASS")
    print("- OrganizationStep: PASS")
    print("- LessonPlanContent: PASS")
    print("- Dictionary serialization: PASS")

    print("\nKẾT QUẢ: 10/10 TEST PASS")


if __name__ == "__main__":
    main()