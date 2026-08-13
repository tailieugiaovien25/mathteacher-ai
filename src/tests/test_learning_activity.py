import sys

sys.path.insert(0, "src")

from models.learning_activity import (
    LearningActivity,
)


def expect_value_error(
    activity: LearningActivity,
) -> None:
    try:
        activity.validate()
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError but validation passed."
    )


def main() -> None:
    # =========================================================
    # 1. MO_DAU - KHỞI ĐỘNG
    # =========================================================

    opening = LearningActivity(
        activity_id="T7_DAI_B03_P01_ACT01",
        lesson_key="T7_DAI_B03",
        period_in_lesson=1,
        activity_type="MO_DAU",
        title="Khởi động",
        objective_ids=[
            "T7_DAI_B03_OBJ_KT01",
        ],
        yccd_ids=[
            "T7_DAI_B03_Y01",
        ],
        task_transfer=(
            "Giáo viên giao nhiệm vụ mở đầu."
        ),
        task_execution=(
            "Học sinh thực hiện nhiệm vụ."
        ),
        report_discussion=(
            "Học sinh báo cáo, trao đổi."
        ),
        conclusion=(
            "Giáo viên chốt vấn đề cần tìm hiểu "
            "trong bài học."
        ),
        order=1,
        status="draft",
    )

    opening.validate()

    # =========================================================
    # 2. MO_DAU - NHẮC LẠI KIẾN THỨC
    # =========================================================

    review_opening = LearningActivity(
        activity_id="T7_DAI_B03_P02_ACT01",
        lesson_key="T7_DAI_B03",
        period_in_lesson=2,
        activity_type="MO_DAU",
        title="Nhắc lại kiến thức",
        yccd_ids=[
            "T7_DAI_B03_Y01",
        ],
        conclusion=(
            "Giáo viên chốt lại kiến thức cần thiết "
            "để tiếp tục thực hiện nhiệm vụ của tiết học."
        ),
        order=1,
        status="draft",
    )

    review_opening.validate()

    # =========================================================
    # 3. HÌNH THÀNH KIẾN THỨC
    # =========================================================

    knowledge = LearningActivity(
        activity_id="T7_DAI_B03_P02_ACT02",
        lesson_key="T7_DAI_B03",
        period_in_lesson=2,
        activity_type="HINH_THANH_KIEN_THUC",
        title="Nhân và chia hai lũy thừa cùng cơ số",
        objective_ids=[
            "T7_DAI_B03_OBJ_KT02",
        ],
        yccd_ids=[
            "T7_DAI_B03_Y02",
        ],
        conclusion=(
            "Giáo viên chốt quy tắc nhân và chia "
            "hai lũy thừa cùng cơ số."
        ),
        order=2,
        status="draft",
    )

    knowledge.validate()

    # =========================================================
    # 4. LUYỆN TẬP
    # =========================================================

    practice = LearningActivity(
        activity_id="T7_DAI_B03_P02_ACT03",
        lesson_key="T7_DAI_B03",
        period_in_lesson=2,
        activity_type="LUYEN_TAP",
        title="Luyện tập",
        objective_ids=[
            "T7_DAI_B03_OBJ_KT02",
        ],
        yccd_ids=[
            "T7_DAI_B03_Y02",
        ],
        conclusion=(
            "Giáo viên chốt cách áp dụng quy tắc "
            "và những lỗi cần tránh."
        ),
        order=3,
        status="draft",
    )

    practice.validate()

    # =========================================================
    # 5. VẬN DỤNG
    # =========================================================

    application = LearningActivity(
        activity_id="T7_DAI_B03_P02_ACT04",
        lesson_key="T7_DAI_B03",
        period_in_lesson=2,
        activity_type="VAN_DUNG",
        title="Vận dụng",
        objective_ids=[
            "T7_DAI_B03_OBJ_KT02",
        ],
        yccd_ids=[
            "T7_DAI_B03_Y02",
        ],
        conclusion=(
            "Giáo viên chốt cách vận dụng kiến thức "
            "đã học vào tình huống phù hợp."
        ),
        order=4,
        status="draft",
    )

    application.validate()

    # =========================================================
    # 6. KHOI_DONG KHÔNG CÒN LÀ ACTIVITY_TYPE
    # =========================================================

    expect_value_error(
        LearningActivity(
            activity_id="TEST_OLD_TYPE",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            activity_type="KHOI_DONG",
            title="Khởi động",
            conclusion="Chốt.",
        )
    )

    # =========================================================
    # 7. ACTIVITY_TYPE SAI
    # =========================================================

    expect_value_error(
        LearningActivity(
            activity_id="TEST_TYPE",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            activity_type="THAO_LUAN",
            title="Hoạt động mẫu",
            conclusion="Chốt.",
        )
    )

    # =========================================================
    # 8. PERIOD = 0
    # =========================================================

    expect_value_error(
        LearningActivity(
            activity_id="TEST_PERIOD",
            lesson_key="T7_DAI_B03",
            period_in_lesson=0,
            activity_type="LUYEN_TAP",
            title="Luyện tập",
            conclusion="Chốt.",
        )
    )

    # =========================================================
    # 9. PERIOD KHÔNG PHẢI SỐ
    # =========================================================

    expect_value_error(
        LearningActivity(
            activity_id="TEST_PERIOD_TEXT",
            lesson_key="T7_DAI_B03",
            period_in_lesson="abc",
            activity_type="LUYEN_TAP",
            title="Luyện tập",
            conclusion="Chốt.",
        )
    )

    # =========================================================
    # 10. TITLE RỖNG
    # =========================================================

    expect_value_error(
        LearningActivity(
            activity_id="TEST_TITLE",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            activity_type="LUYEN_TAP",
            title="",
            conclusion="Chốt.",
        )
    )

    # =========================================================
    # 11. OBJECTIVE_IDS TRÙNG
    # =========================================================

    expect_value_error(
        LearningActivity(
            activity_id="TEST_OBJ_DUP",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            activity_type="LUYEN_TAP",
            title="Luyện tập",
            objective_ids=[
                "OBJ01",
                "OBJ01",
            ],
            conclusion="Chốt.",
        )
    )

    # =========================================================
    # 12. YCCD_IDS TRÙNG
    # =========================================================

    expect_value_error(
        LearningActivity(
            activity_id="TEST_YCCD_DUP",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            activity_type="LUYEN_TAP",
            title="Luyện tập",
            yccd_ids=[
                "Y01",
                "Y01",
            ],
            conclusion="Chốt.",
        )
    )

    # =========================================================
    # 13. ORDER = 0
    # =========================================================

    expect_value_error(
        LearningActivity(
            activity_id="TEST_ORDER",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            activity_type="LUYEN_TAP",
            title="Luyện tập",
            conclusion="Chốt.",
            order=0,
        )
    )

    # =========================================================
    # 14. STATUS SAI
    # =========================================================

    expect_value_error(
        LearningActivity(
            activity_id="TEST_STATUS",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            activity_type="LUYEN_TAP",
            title="Luyện tập",
            conclusion="Chốt.",
            status="active",
        )
    )

    # =========================================================
    # 15. CONCLUSION RỖNG PHẢI BỊ CHẶN
    # =========================================================

    expect_value_error(
        LearningActivity(
            activity_id="TEST_NO_CONCLUSION",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            activity_type="HINH_THANH_KIEN_THUC",
            title="Hình thành kiến thức",
            conclusion="",
        )
    )

    # =========================================================
    # 16. to_dict()
    # =========================================================

    data = knowledge.to_dict()

    assert (
        data["ACTIVITY_TYPE"]
        == "HINH_THANH_KIEN_THUC"
    )

    assert (
        data["CONCLUSION"]
        == knowledge.conclusion
    )

    print("=" * 72)
    print(
        "LP-03G.1B - "
        "LEARNING ACTIVITY MODEL TEST"
    )
    print("=" * 72)

    print("- MO_DAU - Khởi động: PASS")
    print("- MO_DAU - Nhắc lại kiến thức: PASS")
    print("- HINH_THANH_KIEN_THUC: PASS")
    print("- LUYEN_TAP: PASS")
    print("- VAN_DUNG: PASS")
    print("- KHOI_DONG cũ bị chặn: PASS")
    print("- ACTIVITY_TYPE sai bị chặn: PASS")
    print("- PERIOD = 0 bị chặn: PASS")
    print("- PERIOD không phải số bị chặn: PASS")
    print("- TITLE rỗng bị chặn: PASS")
    print("- OBJECTIVE_IDS trùng bị chặn: PASS")
    print("- YCCD_IDS trùng bị chặn: PASS")
    print("- ORDER = 0 bị chặn: PASS")
    print("- STATUS sai bị chặn: PASS")
    print("- CONCLUSION rỗng bị chặn: PASS")
    print("- to_dict() giữ nội dung chốt: PASS")

    print(
        "\nKẾT QUẢ: 16/16 TEST PASS"
    )


if __name__ == "__main__":
    main()