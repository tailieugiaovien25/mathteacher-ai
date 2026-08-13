import sys

sys.path.insert(0, "src")

from models.lesson_objective import LessonObjective


def expect_value_error(
    objective: LessonObjective,
) -> None:
    try:
        objective.validate()
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError but validation passed."
    )


def main() -> None:
    # =========================================================
    # 1. KIẾN THỨC HỢP LỆ
    # =========================================================

    knowledge = LessonObjective(
        objective_id="T7_DAI_B03_OBJ_KT01",
        lesson_key="T7_DAI_B03",
        objective_type="KIEN_THUC",
        content=(
            "Mô tả được phép tính lũy thừa với số mũ "
            "tự nhiên của một số hữu tỉ."
        ),
        source_yccd_ids=[
            "T7_DAI_B03_Y01",
        ],
        order=1,
        status="draft",
    )

    knowledge.validate()

    # =========================================================
    # 2. NĂNG LỰC HỢP LỆ
    # =========================================================

    competency = LessonObjective(
        objective_id="T7_DAI_B03_OBJ_NL01",
        lesson_key="T7_DAI_B03",
        objective_type="NANG_LUC",
        content=(
            "Thực hiện và giải thích được các phép tính "
            "với lũy thừa trong tình huống phù hợp."
        ),
        source_yccd_ids=[
            "T7_DAI_B03_Y02",
            "T7_DAI_B03_Y03",
        ],
        order=2,
        status="draft",
    )

    competency.validate()

    # =========================================================
    # 3. PHẨM CHẤT HỢP LỆ, KHÔNG BẮT BUỘC YCCD_ID
    # =========================================================

    quality = LessonObjective(
        objective_id="T7_DAI_B03_OBJ_PC01",
        lesson_key="T7_DAI_B03",
        objective_type="PHAM_CHAT",
        content=(
            "Chăm chỉ và có trách nhiệm trong thực hiện "
            "nhiệm vụ học tập."
        ),
        source_yccd_ids=[],
        order=3,
        status="draft",
    )

    quality.validate()

    # =========================================================
    # 4. KIẾN THỨC KHÔNG CÓ YCCĐ NGUỒN -> LỖI
    # =========================================================

    expect_value_error(
        LessonObjective(
            objective_id="TEST_KT",
            lesson_key="T7_DAI_B03",
            objective_type="KIEN_THUC",
            content="Mục tiêu kiến thức.",
            source_yccd_ids=[],
        )
    )

    # =========================================================
    # 5. LOẠI MỤC TIÊU SAI
    # =========================================================

    expect_value_error(
        LessonObjective(
            objective_id="TEST_TYPE",
            lesson_key="T7_DAI_B03",
            objective_type="KY_NANG",
            content="Mục tiêu mẫu.",
            source_yccd_ids=[
                "T7_DAI_B03_Y01",
            ],
        )
    )

    # =========================================================
    # 6. SOURCE_YCCD_IDS CÓ ID RỖNG
    # =========================================================

    expect_value_error(
        LessonObjective(
            objective_id="TEST_EMPTY_SOURCE",
            lesson_key="T7_DAI_B03",
            objective_type="KIEN_THUC",
            content="Mục tiêu mẫu.",
            source_yccd_ids=[
                "",
            ],
        )
    )

    # =========================================================
    # 7. SOURCE_YCCD_IDS BỊ TRÙNG
    # =========================================================

    expect_value_error(
        LessonObjective(
            objective_id="TEST_DUP_SOURCE",
            lesson_key="T7_DAI_B03",
            objective_type="KIEN_THUC",
            content="Mục tiêu mẫu.",
            source_yccd_ids=[
                "T7_DAI_B03_Y01",
                "T7_DAI_B03_Y01",
            ],
        )
    )

    # =========================================================
    # 8. ORDER = 0
    # =========================================================

    expect_value_error(
        LessonObjective(
            objective_id="TEST_ORDER",
            lesson_key="T7_DAI_B03",
            objective_type="NANG_LUC",
            content="Mục tiêu mẫu.",
            source_yccd_ids=[],
            order=0,
        )
    )

    # =========================================================
    # 9. STATUS SAI
    # =========================================================

    expect_value_error(
        LessonObjective(
            objective_id="TEST_STATUS",
            lesson_key="T7_DAI_B03",
            objective_type="PHAM_CHAT",
            content="Mục tiêu mẫu.",
            source_yccd_ids=[],
            status="active",
        )
    )

    # =========================================================
    # 10. to_dict()
    # =========================================================

    data = knowledge.to_dict()

    assert (
        data["OBJECTIVE_ID"]
        == "T7_DAI_B03_OBJ_KT01"
    )

    assert (
        data["OBJECTIVE_TYPE"]
        == "KIEN_THUC"
    )

    assert (
        data["SOURCE_YCCD_IDS"]
        == ["T7_DAI_B03_Y01"]
    )

    print("=" * 70)
    print(
        "LP-03F.1 - "
        "LESSON OBJECTIVE MODEL TEST"
    )
    print("=" * 70)

    print("- KIEN_THUC hợp lệ: PASS")
    print("- NANG_LUC hợp lệ: PASS")
    print("- PHAM_CHAT hợp lệ: PASS")
    print("- KIEN_THUC thiếu nguồn bị chặn: PASS")
    print("- OBJECTIVE_TYPE sai bị chặn: PASS")
    print("- SOURCE_YCCD_IDS có ID rỗng bị chặn: PASS")
    print("- SOURCE_YCCD_IDS trùng bị chặn: PASS")
    print("- ORDER = 0 bị chặn: PASS")
    print("- STATUS sai bị chặn: PASS")
    print("- to_dict() đúng: PASS")

    print(
        "\nKẾT QUẢ: 10/10 TEST PASS"
    )


if __name__ == "__main__":
    main()