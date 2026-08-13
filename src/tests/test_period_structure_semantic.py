import sys

sys.path.insert(0, "src")

from models.learning_activity import (
    LearningActivity,
)
from models.period_structure import (
    PeriodStructure,
)


def expect_value_error(
    period: PeriodStructure,
) -> None:
    try:
        period.validate()
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
        objective_text=(
            "Mục tiêu của hoạt động."
        ),
        content=(
            "Nội dung của hoạt động."
        ),
        expected_product=(
            "Sản phẩm dự kiến của học sinh."
        ),
        teacher_conclusion=(
            "Giáo viên chốt nội dung quan trọng "
            "của hoạt động."
        ),
        order=order,
        status="draft",
    )


def main() -> None:
    # =========================================================
    # 1. TIẾT LÝ THUYẾT HỢP LỆ
    # =========================================================

    theory = PeriodStructure(
        lesson_key="T7_DAI_B03",
        period_in_lesson=1,
        period_type="LY_THUYET",
        activities=[
            make_activity(
                "P01_A01",
                1,
                "MO_DAU",
                "Khởi động",
                1,
            ),
            make_activity(
                "P01_A02",
                1,
                "HINH_THANH_KIEN_THUC",
                "Hình thành kiến thức",
                2,
            ),
            make_activity(
                "P01_A03",
                1,
                "LUYEN_TAP",
                "Luyện tập",
                3,
            ),
            make_activity(
                "P01_A04",
                1,
                "VAN_DUNG",
                "Vận dụng",
                4,
            ),
        ],
        status="draft",
    )

    theory.validate()

    # =========================================================
    # 2. TIẾT LUYỆN TẬP KHÔNG CÓ HTKT VẪN HỢP LỆ
    # =========================================================

    practice = PeriodStructure(
        lesson_key="T7_DAI_B03",
        period_in_lesson=2,
        period_type="LUYEN_TAP",
        activities=[
            make_activity(
                "P02_A01",
                2,
                "MO_DAU",
                "Nhắc lại kiến thức",
                1,
            ),
            make_activity(
                "P02_A02",
                2,
                "LUYEN_TAP",
                "Luyện tập cơ bản",
                2,
            ),
            make_activity(
                "P02_A03",
                2,
                "LUYEN_TAP",
                "Luyện tập tổng hợp",
                3,
            ),
            make_activity(
                "P02_A04",
                2,
                "VAN_DUNG",
                "Vận dụng",
                4,
            ),
        ],
        status="draft",
    )

    practice.validate()

    # =========================================================
    # 3. TIẾT ÔN TẬP KHÔNG CÓ HTKT VẪN HỢP LỆ
    # =========================================================

    review = PeriodStructure(
        lesson_key="T7_DAI_B03",
        period_in_lesson=3,
        period_type="ON_TAP",
        activities=[
            make_activity(
                "P03_A01",
                3,
                "MO_DAU",
                "Hệ thống kiến thức",
                1,
            ),
            make_activity(
                "P03_A02",
                3,
                "LUYEN_TAP",
                "Ôn tập dạng 1",
                2,
            ),
            make_activity(
                "P03_A03",
                3,
                "LUYEN_TAP",
                "Ôn tập dạng 2",
                3,
            ),
            make_activity(
                "P03_A04",
                3,
                "VAN_DUNG",
                "Vận dụng tổng hợp",
                4,
            ),
        ],
        status="draft",
    )

    review.validate()

    # =========================================================
    # 4. LY_THUYET THIẾU HÌNH THÀNH KIẾN THỨC
    # =========================================================

    expect_value_error(
        PeriodStructure(
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            period_type="LY_THUYET",
            activities=[
                make_activity(
                    "TEST_A01",
                    1,
                    "MO_DAU",
                    "Mở đầu",
                    1,
                ),
                make_activity(
                    "TEST_A02",
                    1,
                    "LUYEN_TAP",
                    "Luyện tập",
                    2,
                ),
                make_activity(
                    "TEST_A03",
                    1,
                    "VAN_DUNG",
                    "Vận dụng",
                    3,
                ),
            ],
        )
    )

    # =========================================================
    # 5. THIẾU MỞ ĐẦU
    # =========================================================

    expect_value_error(
        PeriodStructure(
            lesson_key="T7_DAI_B03",
            period_in_lesson=2,
            period_type="LUYEN_TAP",
            activities=[
                make_activity(
                    "TEST_NO_OPEN_01",
                    2,
                    "LUYEN_TAP",
                    "Luyện tập",
                    1,
                ),
                make_activity(
                    "TEST_NO_OPEN_02",
                    2,
                    "VAN_DUNG",
                    "Vận dụng",
                    2,
                ),
            ],
        )
    )

    # =========================================================
    # 6. THIẾU LUYỆN TẬP
    # =========================================================

    expect_value_error(
        PeriodStructure(
            lesson_key="T7_DAI_B03",
            period_in_lesson=2,
            period_type="LUYEN_TAP",
            activities=[
                make_activity(
                    "TEST_NO_PRACTICE_01",
                    2,
                    "MO_DAU",
                    "Mở đầu",
                    1,
                ),
                make_activity(
                    "TEST_NO_PRACTICE_02",
                    2,
                    "VAN_DUNG",
                    "Vận dụng",
                    2,
                ),
            ],
        )
    )

    # =========================================================
    # 7. THIẾU VẬN DỤNG
    # =========================================================

    expect_value_error(
        PeriodStructure(
            lesson_key="T7_DAI_B03",
            period_in_lesson=2,
            period_type="LUYEN_TAP",
            activities=[
                make_activity(
                    "TEST_NO_APP_01",
                    2,
                    "MO_DAU",
                    "Mở đầu",
                    1,
                ),
                make_activity(
                    "TEST_NO_APP_02",
                    2,
                    "LUYEN_TAP",
                    "Luyện tập",
                    2,
                ),
            ],
        )
    )

    # =========================================================
    # 8. ACTIVITY KHÁC TIẾT
    # =========================================================

    expect_value_error(
        PeriodStructure(
            lesson_key="T7_DAI_B03",
            period_in_lesson=2,
            period_type="LUYEN_TAP",
            activities=[
                make_activity(
                    "WRONG_PERIOD",
                    1,
                    "MO_DAU",
                    "Mở đầu",
                    1,
                ),
                make_activity(
                    "RIGHT_PERIOD_01",
                    2,
                    "LUYEN_TAP",
                    "Luyện tập",
                    2,
                ),
                make_activity(
                    "RIGHT_PERIOD_02",
                    2,
                    "VAN_DUNG",
                    "Vận dụng",
                    3,
                ),
            ],
        )
    )

    # =========================================================
    # 9. ACTIVITY KHÁC LESSON_KEY
    # =========================================================

    wrong_key = LearningActivity(
        activity_id="WRONG_KEY",
        lesson_key="T7_DAI_B04",
        period_in_lesson=2,
        activity_type="MO_DAU",
        title="Mở đầu",
        teacher_conclusion="Chốt.",
        order=1,
    )

    expect_value_error(
        PeriodStructure(
            lesson_key="T7_DAI_B03",
            period_in_lesson=2,
            period_type="LUYEN_TAP",
            activities=[
                wrong_key,
                make_activity(
                    "RIGHT_KEY_01",
                    2,
                    "LUYEN_TAP",
                    "Luyện tập",
                    2,
                ),
                make_activity(
                    "RIGHT_KEY_02",
                    2,
                    "VAN_DUNG",
                    "Vận dụng",
                    3,
                ),
            ],
        )
    )

    # =========================================================
    # 10. TRÙNG ACTIVITY_ID
    # =========================================================

    expect_value_error(
        PeriodStructure(
            lesson_key="T7_DAI_B03",
            period_in_lesson=2,
            period_type="LUYEN_TAP",
            activities=[
                make_activity(
                    "DUP",
                    2,
                    "MO_DAU",
                    "Mở đầu",
                    1,
                ),
                make_activity(
                    "DUP",
                    2,
                    "LUYEN_TAP",
                    "Luyện tập",
                    2,
                ),
                make_activity(
                    "APP",
                    2,
                    "VAN_DUNG",
                    "Vận dụng",
                    3,
                ),
            ],
        )
    )

    # =========================================================
    # 11. TRÙNG ORDER
    # =========================================================

    expect_value_error(
        PeriodStructure(
            lesson_key="T7_DAI_B03",
            period_in_lesson=2,
            period_type="LUYEN_TAP",
            activities=[
                make_activity(
                    "ORDER_01",
                    2,
                    "MO_DAU",
                    "Mở đầu",
                    1,
                ),
                make_activity(
                    "ORDER_02",
                    2,
                    "LUYEN_TAP",
                    "Luyện tập",
                    1,
                ),
                make_activity(
                    "ORDER_03",
                    2,
                    "VAN_DUNG",
                    "Vận dụng",
                    3,
                ),
            ],
        )
    )

    # =========================================================
    # 12. NHIỀU LUYEN_TAP HỢP LỆ
    # =========================================================

    practice_activities = (
        practice.get_activities_by_type(
            "LUYEN_TAP"
        )
    )

    assert len(
        practice_activities
    ) == 2

    # =========================================================
    # 13. get_activities() ĐÚNG ORDER
    # =========================================================

    ordered = review.get_activities()

    assert [
        item.order
        for item in ordered
    ] == [
        1,
        2,
        3,
        4,
    ]

    # =========================================================
    # 14. to_dict()
    # =========================================================

    data = review.to_dict()

    assert (
        data["PERIOD_TYPE"]
        == "ON_TAP"
    )

    assert (
        data["PERIOD_IN_LESSON"]
        == 3
    )

    assert len(
        data["ACTIVITIES"]
    ) == 4

    # =========================================================
    # 15. KHÔNG CHỨA LOGIC TEMPLATE
    # =========================================================

    forbidden_keys = {
        "COLUMN_1",
        "COLUMN_2",
        "TABLE_LAYOUT",
        "COLUMN_TITLE",
        "FONT",
        "ALIGNMENT",
    }

    assert forbidden_keys.isdisjoint(
        data.keys()
    )

    print("=" * 72)
    print(
        "LP-03G-ARCH - "
        "PERIOD STRUCTURE SEMANTIC TEST"
    )
    print("=" * 72)

    print("- LY_THUYET đủ 4 nhóm hoạt động: PASS")
    print("- LUYEN_TAP không có HTKT vẫn hợp lệ: PASS")
    print("- ON_TAP không có HTKT vẫn hợp lệ: PASS")
    print("- LY_THUYET thiếu HTKT bị chặn: PASS")
    print("- Thiếu MO_DAU bị chặn: PASS")
    print("- Thiếu LUYEN_TAP bị chặn: PASS")
    print("- Thiếu VAN_DUNG bị chặn: PASS")
    print("- Activity khác tiết bị chặn: PASS")
    print("- Activity khác LESSON_KEY bị chặn: PASS")
    print("- ACTIVITY_ID trùng bị chặn: PASS")
    print("- ORDER trùng bị chặn: PASS")
    print("- Nhiều LUYEN_TAP hợp lệ: PASS")
    print("- get_activities() đúng ORDER: PASS")
    print("- to_dict() semantic đúng: PASS")
    print("- Không chứa logic template: PASS")

    print(
        "\nKẾT QUẢ: 15/15 TEST PASS"
    )


if __name__ == "__main__":
    main()