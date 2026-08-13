import sys
from pathlib import Path

sys.path.insert(0, "src")

from intelligence.lesson_model_builder import LessonModelBuilder
from intelligence.lesson_plan_builder import LessonPlanBuilder
from models.math_lesson_plan_schema import (
    create_math_lesson_plan_schema,
)


EXCEL_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)

SHEET_NAME = "LuuBG"
DATA_ROW = 81


def main() -> None:
    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file Excel: {EXCEL_FILE}"
        )

    # 1. Đọc bài học thật từ Excel LuuBG.
    lesson_builder = LessonModelBuilder()

    lesson = lesson_builder.build(
        file_path=str(EXCEL_FILE),
        sheet_name=SHEET_NAME,
        data_row=DATA_ROW,
    )

    # 2. Nạp schema giáo án Toán.
    schema = create_math_lesson_plan_schema()

    # 3. Tạo khung giáo án.
    plan_builder = LessonPlanBuilder()

    lesson_plan = plan_builder.build(
        lesson=lesson,
        schema=schema,
    )

    print("=" * 70)
    print("LP-02B - LESSON PLAN FROM REAL EXCEL DATA")
    print("=" * 70)

    print(f"Môn: {lesson_plan.subject}")
    print(f"Lớp: {lesson_plan.grade}")
    print(f"Bài: {lesson_plan.lesson_name}")
    print(f"Số tiết: {lesson_plan.total_periods}")

    print("\nI. MỤC TIÊU")

    print("\n1. Kiến thức")
    for item in lesson_plan.objectives.knowledge:
        print(f"- {item}")

    print("\nII. THIẾT BỊ DẠY HỌC VÀ HỌC LIỆU")

    print("\n1. Giáo viên")
    for item in lesson_plan.resources.teacher:
        print(f"- {item}")

    print("\n2. Học sinh")
    for item in lesson_plan.resources.students:
        print(f"- {item}")

    print("\nIII. TIẾN TRÌNH DẠY HỌC")

    for activity in lesson_plan.activities:
        print(
            f"- {activity.title}"
            f" [{activity.organization_layout}]"
        )

    # Kiểm tra tích hợp cơ bản.
    assert lesson_plan.subject == "Toán"
    assert lesson_plan.grade == "8C4"
    assert lesson_plan.lesson_name
    assert lesson_plan.total_periods == 2

    assert len(lesson_plan.activities) == 4

    assert (
        lesson_plan.activities[0].organization_layout
        == "single"
    )

    assert (
        lesson_plan.activities[1].organization_layout
        == "two_column"
    )

    assert (
        lesson_plan.metadata["source_row"]
        == DATA_ROW
    )

    print("\nKẾT QUẢ KIỂM TRA")
    print("- Đọc dữ liệu Excel thật: PASS")
    print("- Tạo LessonModel: PASS")
    print("- Nạp Math Schema v1.1: PASS")
    print("- Tạo LessonPlanContent: PASS")
    print("- Tạo đủ 4 hoạt động: PASS")
    print("- Áp dụng layout: PASS")
    print("- Truy vết hàng nguồn: PASS")

    print("\nKẾT QUẢ: 7/7 TEST PASS")


if __name__ == "__main__":
    main()