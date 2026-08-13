import sys
from pathlib import Path

sys.path.insert(0, "src")

from services.lesson_objective_resolver import (
    LessonObjectiveResolver,
)
from services.objective_builder import (
    ObjectiveBuilder,
)


EXCEL_FILE = Path(
    "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
)


def main() -> None:
    resolver = LessonObjectiveResolver()
    builder = ObjectiveBuilder()

    # =========================================================
    # 1. TOÀN BÀI
    # =========================================================

    lesson_selection = resolver.get_objectives(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        mode="LESSON",
        status="draft",
    )

    lesson_objectives = (
        builder.build_knowledge_objectives(
            lesson_selection
        )
    )

    assert len(lesson_objectives) == 3

    assert [
        item.objective_id
        for item in lesson_objectives
    ] == [
        "T7_DAI_B03_OBJ_KT01",
        "T7_DAI_B03_OBJ_KT02",
        "T7_DAI_B03_OBJ_KT03",
    ]

    assert [
        item.source_yccd_ids
        for item in lesson_objectives
    ] == [
        ["T7_DAI_B03_Y01"],
        ["T7_DAI_B03_Y02"],
        ["T7_DAI_B03_Y03"],
    ]

    # =========================================================
    # 2. TIẾT 1
    # =========================================================

    period_1_selection = resolver.get_objectives(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        mode="PERIOD",
        period_in_lesson=1,
        status="draft",
    )

    period_1_objectives = (
        builder.build_knowledge_objectives(
            period_1_selection
        )
    )

    assert len(period_1_objectives) == 1

    assert (
        period_1_objectives[0]
        .source_yccd_ids
        == ["T7_DAI_B03_Y01"]
    )

    # =========================================================
    # 3. TIẾT 2
    # =========================================================

    period_2_selection = resolver.get_objectives(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        mode="PERIOD",
        period_in_lesson=2,
        status="draft",
    )

    period_2_objectives = (
        builder.build_knowledge_objectives(
            period_2_selection
        )
    )

    assert len(period_2_objectives) == 2

    assert [
        item.source_yccd_ids
        for item in period_2_objectives
    ] == [
        ["T7_DAI_B03_Y01"],
        ["T7_DAI_B03_Y02"],
    ]

    # =========================================================
    # 4. TIẾT 3
    # =========================================================

    period_3_selection = resolver.get_objectives(
        file_path=EXCEL_FILE,
        lesson_key="T7_DAI_B03",
        mode="PERIOD",
        period_in_lesson=3,
        status="draft",
    )

    period_3_objectives = (
        builder.build_knowledge_objectives(
            period_3_selection
        )
    )

    assert len(period_3_objectives) == 2

    assert [
        item.source_yccd_ids
        for item in period_3_objectives
    ] == [
        ["T7_DAI_B03_Y02"],
        ["T7_DAI_B03_Y03"],
    ]

    # =========================================================
    # 5. NỘI DUNG KHÔNG RỖNG
    # =========================================================

    assert all(
        item.content.strip()
        for item in lesson_objectives
    )

    # =========================================================
    # 6. TẤT CẢ LÀ KIẾN THỨC
    # =========================================================

    assert all(
        item.normalized_type
        == "KIEN_THUC"
        for item in lesson_objectives
    )

    # =========================================================
    # 7. COVERAGE TOÀN BÀI
    # =========================================================

    covered_yccd_ids = {
        source_id
        for objective in lesson_objectives
        for source_id
        in objective.source_yccd_ids
    }

    assert covered_yccd_ids == {
        "T7_DAI_B03_Y01",
        "T7_DAI_B03_Y02",
        "T7_DAI_B03_Y03",
    }

    # =========================================================
    # KẾT QUẢ
    # =========================================================

    print("=" * 72)
    print(
        "LP-03F.2 - "
        "OBJECTIVE BUILDER REAL TEST"
    )
    print("=" * 72)

    print(
        "- LESSON tạo đúng 3 mục tiêu: PASS"
    )
    print(
        "- OBJECTIVE_ID đúng thứ tự: PASS"
    )
    print(
        "- Truy vết LESSON Y01-Y03: PASS"
    )
    print(
        "- PERIOD 1 -> Y01: PASS"
    )
    print(
        "- PERIOD 2 -> Y01 + Y02: PASS"
    )
    print(
        "- PERIOD 3 -> Y02 + Y03: PASS"
    )
    print(
        "- Nội dung mục tiêu không rỗng: PASS"
    )
    print(
        "- Tất cả là KIEN_THUC: PASS"
    )
    print(
        "- Coverage YCCĐ toàn bài đầy đủ: PASS"
    )

    print(
        "\nKẾT QUẢ: 9/9 TEST PASS"
    )


if __name__ == "__main__":
    main()