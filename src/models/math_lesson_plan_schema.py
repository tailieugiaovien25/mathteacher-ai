from models.lesson_plan_schema import (
    ActivitySchema,
    LessonPlanSchema,
    LessonPlanSectionSchema,
)


def create_math_lesson_plan_schema() -> LessonPlanSchema:
    """Tạo Math Lesson Plan Schema v1.1 mặc định."""

    sections = [
        LessonPlanSectionSchema(
            key="objectives",
            title="I. MỤC TIÊU",
            order=1,
        ),
        LessonPlanSectionSchema(
            key="resources",
            title="II. THIẾT BỊ DẠY HỌC VÀ HỌC LIỆU",
            order=2,
        ),
        LessonPlanSectionSchema(
            key="learning_process",
            title="III. TIẾN TRÌNH DẠY HỌC",
            order=3,
        ),
    ]

    two_column_headers = [
        "HOẠT ĐỘNG CỦA GIÁO VIÊN VÀ HỌC SINH",
        "DỰ KIẾN SẢN PHẨM",
    ]

    activities = [
        ActivitySchema(
            key="opening",
            title="Hoạt động 1. Mở đầu",
            default_layout="single",
            allowed_layouts=[
                "single",
            ],
        ),
        ActivitySchema(
            key="knowledge_formation",
            title="Hoạt động 2. Hình thành kiến thức",
            default_layout="two_column",
            allowed_layouts=[
                "two_column",
            ],
            allow_subactivities=True,
            column_headers=two_column_headers.copy(),
        ),
        ActivitySchema(
            key="practice",
            title="Hoạt động 3. Luyện tập",
            default_layout="single",
            allowed_layouts=[
                "single",
                "two_column",
            ],
            column_headers=two_column_headers.copy(),
        ),
        ActivitySchema(
            key="application",
            title="Hoạt động 4. Vận dụng",
            default_layout="single",
            allowed_layouts=[
                "single",
                "two_column",
            ],
            column_headers=two_column_headers.copy(),
        ),
    ]

    return LessonPlanSchema(
        schema_id="math_lesson_plan_v1_1",
        name="Math Lesson Plan Schema",
        subject="Toán",
        version="1.1",
        sections=sections,
        activities=activities,
        metadata={
            "status": "temporary_configurable",
        },
    )