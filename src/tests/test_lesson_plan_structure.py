import sys

sys.path.insert(0, "src")

from models.learning_activity import (
    LearningActivity,
)
from models.lesson_plan_structure import (
    LessonPlanStructure,
)


def expect_value_error(
    plan: LessonPlanStructure,
) -> None:
    try:
        plan.validate()
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError but validation passed."
    )


def make_activity(
    activity_id: str,
    period: int,
    activity_type: str,
    title: str,
    order: int,
) -> LearningActivity:
    return LearningActivity(
        activity_id=activity_id,
        lesson_key="T7_DAI_B03",
        period_in_lesson=period,
        activity_type=activity_type,
        title=title,
        conclusion=(
            "Giáo viên chốt nội dung quan trọng "
            "của hoạt động."
        ),
        order=order,
        status="draft",
    )


def main() -> None:
    # =========================================================
    # 1. FULL_LESSON HỢP LỆ
    # =========================================================

    full_plan = LessonPlanStructure(
        plan_id="T7_DAI_B03_PLAN_FULL",
        lesson_key="T7_DAI_B03",
        plan_mode="FULL_LESSON",
        lesson_type="LY_THUYET",
        total_periods=3,
        period_in_lesson=None,
        activities=[
            make_activity(
                "P01_ACT01",
                1,
                "MO_DAU",
                "Khởi động",
                1,
            ),
            make_activity(
                "P01_ACT02",
                1,
                "HINH_THANH_KIEN_THUC",
                "Lũy thừa với số mũ tự nhiên",
                2,
            ),
            make_activity(
                "P02_ACT01",
                2,
                "MO_DAU",
                "Nhắc lại kiến thức",
                1,
            ),
            make_activity(
                "P02_ACT02",
                2,
                "HINH_THANH_KIEN_THUC",
                "Nhân và chia hai lũy thừa cùng cơ số",
                2,
            ),
            make_activity(
                "P03_ACT01",
                3,
                "MO_DAU",
                "Kết nối kiến thức",
                1,
            ),
            make_activity(
                "P03_ACT02",
                3,
                "LUYEN_TAP",
                "Luyện tập tổng hợp",
                2,
            ),
        ],
        status="draft",
    )

    full_plan.validate()

    # =========================================================
    # 2. SINGLE_PERIOD HỢP LỆ
    # =========================================================

    single_plan = LessonPlanStructure(
        plan_id="T7_DAI_B03_PLAN_P02",
        lesson_key="T7_DAI_B03",
        plan_mode="SINGLE_PERIOD",
        lesson_type="LY_THUYET",
        total_periods=3,
        period_in_lesson=2,
        activities=[
            make_activity(
                "P02_ONLY_ACT01",
                2,
                "MO_DAU",
                "Nhắc lại kiến thức",
                1,
            ),
            make_activity(
                "P02_ONLY_ACT02",
                2,
                "HINH_THANH_KIEN_THUC",
                "Nhân và chia hai lũy thừa cùng cơ số",
                2,
            ),
        ],
        status="draft",
    )

    single_plan.validate()

    # =========================================================
    # 3. FULL_LESSON KHÔNG ĐƯỢC CÓ PERIOD_IN_LESSON
    # =========================================================

    expect_value_error(
        LessonPlanStructure(
            plan_id="TEST_FULL_PERIOD",
            lesson_key="T7_DAI_B03",
            plan_mode="FULL_LESSON",
            lesson_type="LY_THUYET",
            total_periods=3,
            period_in_lesson=1,
        )
    )

    # =========================================================
    # 4. SINGLE_PERIOD BẮT BUỘC CÓ PERIOD_IN_LESSON
    # =========================================================

    expect_value_error(
        LessonPlanStructure(
            plan_id="TEST_SINGLE_NO_PERIOD",
            lesson_key="T7_DAI_B03",
            plan_mode="SINGLE_PERIOD",
            lesson_type="LY_THUYET",
            total_periods=3,
            period_in_lesson=None,
        )
    )

    # =========================================================
    # 5. PERIOD_IN_LESSON > TOTAL_PERIODS
    # =========================================================

    expect_value_error(
        LessonPlanStructure(
            plan_id="TEST_PERIOD_RANGE",
            lesson_key="T7_DAI_B03",
            plan_mode="SINGLE_PERIOD",
            lesson_type="LY_THUYET",
            total_periods=3,
            period_in_lesson=4,
        )
    )

    # =========================================================
    # 6. PLAN_MODE SAI
    # =========================================================

    expect_value_error(
        LessonPlanStructure(
            plan_id="TEST_MODE",
            lesson_key="T7_DAI_B03",
            plan_mode="MULTI",
            lesson_type="LY_THUYET",
            total_periods=3,
        )
    )

    # =========================================================
    # 7. LESSON_TYPE SAI
    # =========================================================

    expect_value_error(
        LessonPlanStructure(
            plan_id="TEST_TYPE",
            lesson_key="T7_DAI_B03",
            plan_mode="FULL_LESSON",
            lesson_type="THUC_HANH",
            total_periods=3,
        )
    )

    # =========================================================
    # 8. FULL_LESSON KHÔNG ĐƯỢC CÓ ACTIVITY PERIOD = None
    # =========================================================

    invalid_activity = LearningActivity(
        activity_id="NO_PERIOD",
        lesson_key="T7_DAI_B03",
        period_in_lesson=None,
        activity_type="MO_DAU",
        title="Khởi động",
        conclusion="Giáo viên chốt nội dung.",
        order=1,
    )

    expect_value_error(
        LessonPlanStructure(
            plan_id="TEST_ACTIVITY_NO_PERIOD",
            lesson_key="T7_DAI_B03",
            plan_mode="FULL_LESSON",
            lesson_type="LY_THUYET",
            total_periods=3,
            activities=[
                invalid_activity,
            ],
        )
    )

    # =========================================================
    # 9. SINGLE_PERIOD KHÔNG ĐƯỢC LẪN TIẾT
    # =========================================================

    expect_value_error(
        LessonPlanStructure(
            plan_id="TEST_MIX_PERIOD",
            lesson_key="T7_DAI_B03",
            plan_mode="SINGLE_PERIOD",
            lesson_type="LY_THUYET",
            total_periods=3,
            period_in_lesson=2,
            activities=[
                make_activity(
                    "WRONG_PERIOD",
                    1,
                    "MO_DAU",
                    "Khởi động",
                    1,
                ),
            ],
        )
    )

    # =========================================================
    # 10. ACTIVITY KHÁC LESSON_KEY
    # =========================================================

    wrong_key_activity = LearningActivity(
        activity_id="WRONG_KEY",
        lesson_key="T7_DAI_B04",
        period_in_lesson=1,
        activity_type="MO_DAU",
        title="Khởi động",
        conclusion="Giáo viên chốt nội dung.",
        order=1,
    )

    expect_value_error(
        LessonPlanStructure(
            plan_id="TEST_WRONG_KEY",
            lesson_key="T7_DAI_B03",
            plan_mode="FULL_LESSON",
            lesson_type="LY_THUYET",
            total_periods=3,
            activities=[
                wrong_key_activity,
            ],
        )
    )

    # =========================================================
    # 11. TRÙNG ACTIVITY_ID
    # =========================================================

    duplicate_a = make_activity(
        "DUP_ACT",
        1,
        "MO_DAU",
        "Khởi động",
        1,
    )

    duplicate_b = make_activity(
        "DUP_ACT",
        1,
        "LUYEN_TAP",
        "Luyện tập",
        2,
    )

    expect_value_error(
        LessonPlanStructure(
            plan_id="TEST_DUP_ACTIVITY",
            lesson_key="T7_DAI_B03",
            plan_mode="FULL_LESSON",
            lesson_type="LY_THUYET",
            total_periods=3,
            activities=[
                duplicate_a,
                duplicate_b,
            ],
        )
    )

    # =========================================================
    # 12. TRÙNG ORDER TRONG CÙNG TIẾT
    # =========================================================

    expect_value_error(
        LessonPlanStructure(
            plan_id="TEST_DUP_ORDER",
            lesson_key="T7_DAI_B03",
            plan_mode="FULL_LESSON",
            lesson_type="LY_THUYET",
            total_periods=3,
            activities=[
                make_activity(
                    "ORDER_A",
                    1,
                    "MO_DAU",
                    "Khởi động",
                    1,
                ),
                make_activity(
                    "ORDER_B",
                    1,
                    "LUYEN_TAP",
                    "Luyện tập",
                    1,
                ),
            ],
        )
    )

    # =========================================================
    # 13. CÙNG ORDER NHƯNG KHÁC TIẾT -> HỢP LỆ
    # =========================================================

    different_period_order = LessonPlanStructure(
        plan_id="TEST_ORDER_DIFFERENT_PERIOD",
        lesson_key="T7_DAI_B03",
        plan_mode="FULL_LESSON",
        lesson_type="LY_THUYET",
        total_periods=3,
        activities=[
            make_activity(
                "ORDER_P1",
                1,
                "MO_DAU",
                "Khởi động",
                1,
            ),
            make_activity(
                "ORDER_P2",
                2,
                "MO_DAU",
                "Nhắc lại kiến thức",
                1,
            ),
        ],
    )

    different_period_order.validate()

    # =========================================================
    # 14. get_period_activities()
    # =========================================================

    period_2 = full_plan.get_period_activities(
        2
    )

    assert len(period_2) == 2

    assert [
        item.activity_id
        for item in period_2
    ] == [
        "P02_ACT01",
        "P02_ACT02",
    ]

    # =========================================================
    # 15. PERIOD NGOÀI PHẠM VI
    # =========================================================

    invalid_period_blocked = False

    try:
        full_plan.get_period_activities(
            4
        )
    except ValueError:
        invalid_period_blocked = True

    assert invalid_period_blocked

    # =========================================================
    # 16. to_dict()
    # =========================================================

    data = single_plan.to_dict()

    assert (
        data["PLAN_MODE"]
        == "SINGLE_PERIOD"
    )

    assert (
        data["PERIOD_IN_LESSON"]
        == 2
    )

    assert len(
        data["ACTIVITIES"]
    ) == 2

    print("=" * 72)
    print(
        "LP-03G.2 - "
        "LESSON PLAN STRUCTURE TEST"
    )
    print("=" * 72)

    print("- FULL_LESSON hợp lệ: PASS")
    print("- SINGLE_PERIOD hợp lệ: PASS")
    print("- FULL_LESSON có period bị chặn: PASS")
    print("- SINGLE_PERIOD thiếu period bị chặn: PASS")
    print("- Period vượt tổng số tiết bị chặn: PASS")
    print("- PLAN_MODE sai bị chặn: PASS")
    print("- LESSON_TYPE sai bị chặn: PASS")
    print("- FULL_LESSON activity thiếu tiết bị chặn: PASS")
    print("- SINGLE_PERIOD lẫn tiết bị chặn: PASS")
    print("- Activity khác LESSON_KEY bị chặn: PASS")
    print("- ACTIVITY_ID trùng bị chặn: PASS")
    print("- ORDER trùng cùng tiết bị chặn: PASS")
    print("- ORDER giống nhau khác tiết hợp lệ: PASS")
    print("- get_period_activities đúng: PASS")
    print("- Period ngoài phạm vi bị chặn: PASS")
    print("- to_dict() đúng: PASS")

    print(
        "\nKẾT QUẢ: 16/16 TEST PASS"
    )


if __name__ == "__main__":
    main()