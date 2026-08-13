import sys

sys.path.insert(0, "src")

from models.implementation_step import (
    ImplementationStep,
)


def expect_value_error(
    step: ImplementationStep,
) -> None:
    try:
        step.validate()
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError but validation passed."
    )


def main() -> None:
    # =========================================================
    # 1. CHUYỂN GIAO HỢP LỆ
    # =========================================================

    transfer = ImplementationStep(
        step_id="STEP01",
        step_order=1,
        step_type="CHUYEN_GIAO",
        instruction=(
            "Giáo viên giao nhiệm vụ cho học sinh."
        ),
        teacher_action=(
            "Nêu yêu cầu và tổ chức nhiệm vụ."
        ),
        student_action=(
            "Tiếp nhận nhiệm vụ."
        ),
        expected_result=(
            "Học sinh hiểu yêu cầu cần thực hiện."
        ),
    )

    transfer.validate()

    # =========================================================
    # 2. THỰC HIỆN HỢP LỆ
    # =========================================================

    execution = ImplementationStep(
        step_id="STEP02",
        step_order=2,
        step_type="THUC_HIEN",
        teacher_action=(
            "Quan sát và hỗ trợ học sinh khi cần."
        ),
        student_action=(
            "Thực hiện nhiệm vụ cá nhân hoặc theo nhóm."
        ),
        expected_result=(
            "Học sinh hoàn thành nhiệm vụ."
        ),
    )

    execution.validate()

    # =========================================================
    # 3. BÁO CÁO - THẢO LUẬN HỢP LỆ
    # =========================================================

    discussion = ImplementationStep(
        step_id="STEP03",
        step_order=3,
        step_type="BAO_CAO_THAO_LUAN",
        teacher_action=(
            "Tổ chức cho học sinh trình bày và trao đổi."
        ),
        student_action=(
            "Báo cáo kết quả và nhận xét."
        ),
        expected_result=(
            "Các kết quả được trình bày và thảo luận."
        ),
    )

    discussion.validate()

    # =========================================================
    # 4. KẾT LUẬN HỢP LỆ
    # =========================================================

    conclusion = ImplementationStep(
        step_id="STEP04",
        step_order=4,
        step_type="KET_LUAN",
        teacher_action=(
            "Nhận xét và chốt nội dung quan trọng."
        ),
        content=(
            "Nội dung kiến thức hoặc phương pháp "
            "cần ghi nhớ."
        ),
    )

    conclusion.validate()

    # =========================================================
    # 5. STEP_ID RỖNG
    # =========================================================

    expect_value_error(
        ImplementationStep(
            step_id="",
            step_order=1,
            step_type="CHUYEN_GIAO",
            content="Nội dung mẫu.",
        )
    )

    # =========================================================
    # 6. STEP_ORDER = 0
    # =========================================================

    expect_value_error(
        ImplementationStep(
            step_id="TEST_ORDER",
            step_order=0,
            step_type="CHUYEN_GIAO",
            content="Nội dung mẫu.",
        )
    )

    # =========================================================
    # 7. STEP_ORDER KHÔNG PHẢI SỐ
    # =========================================================

    expect_value_error(
        ImplementationStep(
            step_id="TEST_ORDER_TEXT",
            step_order="abc",
            step_type="CHUYEN_GIAO",
            content="Nội dung mẫu.",
        )
    )

    # =========================================================
    # 8. STEP_TYPE SAI
    # =========================================================

    expect_value_error(
        ImplementationStep(
            step_id="TEST_TYPE",
            step_order=1,
            step_type="GIANG_BAI",
            content="Nội dung mẫu.",
        )
    )

    # =========================================================
    # 9. KHÔNG CÓ NỘI DUNG SEMANTIC
    # =========================================================

    expect_value_error(
        ImplementationStep(
            step_id="TEST_EMPTY",
            step_order=1,
            step_type="KHAC",
        )
    )

    # =========================================================
    # 10. KHAC VẪN HỢP LỆ NẾU CÓ NỘI DUNG
    # =========================================================

    other = ImplementationStep(
        step_id="STEP_OTHER",
        step_order=5,
        step_type="KHAC",
        note=(
            "Bước bổ sung theo yêu cầu của bài học."
        ),
    )

    other.validate()

    # =========================================================
    # 11. to_dict()
    # =========================================================

    data = transfer.to_dict()

    assert (
        data["STEP_TYPE"]
        == "CHUYEN_GIAO"
    )

    assert (
        data["STEP_ORDER"]
        == 1
    )

    assert (
        data["TEACHER_ACTION"]
        == transfer.teacher_action
    )

    assert (
        data["STUDENT_ACTION"]
        == transfer.student_action
    )

    assert (
        data["EXPECTED_RESULT"]
        == transfer.expected_result
    )

    # =========================================================
    # 12. MODEL KHÔNG CHỨA KHÁI NIỆM CỘT
    # =========================================================

    forbidden_keys = {
        "COLUMN_1",
        "COLUMN_2",
        "TABLE_LAYOUT",
        "COLUMN_TITLE",
    }

    assert (
        forbidden_keys
        .isdisjoint(
            data.keys()
        )
    )

    print("=" * 72)
    print(
        "LP-03G-ARCH - "
        "IMPLEMENTATION STEP TEST"
    )
    print("=" * 72)

    print("- CHUYEN_GIAO hợp lệ: PASS")
    print("- THUC_HIEN hợp lệ: PASS")
    print("- BAO_CAO_THAO_LUAN hợp lệ: PASS")
    print("- KET_LUAN hợp lệ: PASS")
    print("- STEP_ID rỗng bị chặn: PASS")
    print("- STEP_ORDER = 0 bị chặn: PASS")
    print("- STEP_ORDER không phải số bị chặn: PASS")
    print("- STEP_TYPE sai bị chặn: PASS")
    print("- Step không có nội dung bị chặn: PASS")
    print("- STEP_TYPE KHAC hợp lệ: PASS")
    print("- to_dict() đúng: PASS")
    print("- Không chứa logic cột/template: PASS")

    print(
        "\nKẾT QUẢ: 12/12 TEST PASS"
    )


if __name__ == "__main__":
    main()