import sys

sys.path.insert(0, "src")

from models.content_section import (
    ContentSection,
)
from models.implementation_step import (
    ImplementationStep,
)


def expect_value_error(
    section: ContentSection,
) -> None:
    try:
        section.validate()
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError but validation passed."
    )


def make_steps() -> list[ImplementationStep]:
    return [
        ImplementationStep(
            step_id="S02_STEP01",
            step_order=1,
            step_type="CHUYEN_GIAO",
            teacher_action=(
                "Giáo viên giao nhiệm vụ khám phá."
            ),
            student_action=(
                "Học sinh tiếp nhận nhiệm vụ."
            ),
            expected_result=(
                "Học sinh xác định được yêu cầu cần thực hiện."
            ),
        ),
        ImplementationStep(
            step_id="S02_STEP02",
            step_order=2,
            step_type="THUC_HIEN",
            teacher_action=(
                "Giáo viên quan sát và hỗ trợ khi cần."
            ),
            student_action=(
                "Học sinh thực hiện phép biến đổi "
                "và rút ra nhận xét."
            ),
            expected_result=(
                "Học sinh nhận ra quy luật về số mũ."
            ),
        ),
        ImplementationStep(
            step_id="S02_STEP03",
            step_order=3,
            step_type="BAO_CAO_THAO_LUAN",
            teacher_action=(
                "Giáo viên tổ chức báo cáo và thảo luận."
            ),
            student_action=(
                "Học sinh trình bày kết quả, "
                "nhận xét và bổ sung."
            ),
            expected_result=(
                "Học sinh phát biểu được quy tắc."
            ),
        ),
        ImplementationStep(
            step_id="S02_STEP04",
            step_order=4,
            step_type="KET_LUAN",
            teacher_action=(
                "Giáo viên nhận xét và chuẩn hóa kiến thức."
            ),
            content=(
                "Chốt quy tắc nhân hai lũy thừa cùng cơ số."
            ),
        ),
    ]


def main() -> None:
    # =========================================================
    # 1. CONTENT SECTION HỢP LỆ
    # =========================================================

    section = ContentSection(
        section_id="T7_DAI_B03_S02",
        lesson_key="T7_DAI_B03",
        section_order=2,
        section_title=(
            "Nhân và chia hai lũy thừa cùng cơ số"
        ),
        source="SGK",
        yccd_ids=[
            "T7_DAI_B03_Y02",
        ],
        objective_ids=[
            "T7_DAI_B03_OBJ_KT02",
        ],
        objective_text=(
            "Mô tả và thực hiện được phép tính "
            "tích, thương của hai lũy thừa cùng cơ số."
        ),
        content=(
            "Khám phá và khái quát quy tắc nhân, "
            "chia hai lũy thừa cùng cơ số."
        ),
        expected_product=(
            "Học sinh phát biểu được quy tắc "
            "và thực hiện được phép tính."
        ),
        implementation_steps=make_steps(),
        teacher_conclusion=(
            "Giáo viên chốt quy tắc nhân và chia "
            "hai lũy thừa cùng cơ số."
        ),
        status="draft",
    )

    section.validate()

    # =========================================================
    # 2. SECTION_TITLE RỖNG
    # =========================================================

    expect_value_error(
        ContentSection(
            section_id="TEST_TITLE",
            lesson_key="T7_DAI_B03",
            section_order=1,
            section_title="",
            teacher_conclusion="Chốt.",
        )
    )

    # =========================================================
    # 3. SECTION_ORDER = 0
    # =========================================================

    expect_value_error(
        ContentSection(
            section_id="TEST_ORDER",
            lesson_key="T7_DAI_B03",
            section_order=0,
            section_title="Đề mục mẫu",
            teacher_conclusion="Chốt.",
        )
    )

    # =========================================================
    # 4. SOURCE SAI
    # =========================================================

    expect_value_error(
        ContentSection(
            section_id="TEST_SOURCE",
            lesson_key="T7_DAI_B03",
            section_order=1,
            section_title="Đề mục mẫu",
            source="INTERNET",
            teacher_conclusion="Chốt.",
        )
    )

    # =========================================================
    # 5. YCCD_IDS TRÙNG
    # =========================================================

    expect_value_error(
        ContentSection(
            section_id="TEST_YCCD_DUP",
            lesson_key="T7_DAI_B03",
            section_order=1,
            section_title="Đề mục mẫu",
            yccd_ids=[
                "Y01",
                "Y01",
            ],
            teacher_conclusion="Chốt.",
        )
    )

    # =========================================================
    # 6. OBJECTIVE_IDS TRÙNG
    # =========================================================

    expect_value_error(
        ContentSection(
            section_id="TEST_OBJ_DUP",
            lesson_key="T7_DAI_B03",
            section_order=1,
            section_title="Đề mục mẫu",
            objective_ids=[
                "OBJ01",
                "OBJ01",
            ],
            teacher_conclusion="Chốt.",
        )
    )

    # =========================================================
    # 7. STEP_ID TRÙNG
    # =========================================================

    duplicate_steps = make_steps()

    duplicate_steps.append(
        ImplementationStep(
            step_id="S02_STEP01",
            step_order=5,
            step_type="KHAC",
            note="Bước trùng ID.",
        )
    )

    expect_value_error(
        ContentSection(
            section_id="TEST_STEP_ID",
            lesson_key="T7_DAI_B03",
            section_order=1,
            section_title="Đề mục mẫu",
            implementation_steps=(
                duplicate_steps
            ),
            teacher_conclusion="Chốt.",
        )
    )

    # =========================================================
    # 8. STEP_ORDER TRÙNG
    # =========================================================

    duplicate_order_steps = make_steps()

    duplicate_order_steps.append(
        ImplementationStep(
            step_id="STEP_OTHER",
            step_order=4,
            step_type="KHAC",
            note="Bước trùng thứ tự.",
        )
    )

    expect_value_error(
        ContentSection(
            section_id="TEST_STEP_ORDER",
            lesson_key="T7_DAI_B03",
            section_order=1,
            section_title="Đề mục mẫu",
            implementation_steps=(
                duplicate_order_steps
            ),
            teacher_conclusion="Chốt.",
        )
    )

    # =========================================================
    # 9. TEACHER_CONCLUSION RỖNG
    # =========================================================

    expect_value_error(
        ContentSection(
            section_id="TEST_NO_CONCLUSION",
            lesson_key="T7_DAI_B03",
            section_order=1,
            section_title="Đề mục mẫu",
            teacher_conclusion="",
        )
    )

    # =========================================================
    # 10. get_implementation_steps()
    # =========================================================

    ordered_steps = (
        section.get_implementation_steps()
    )

    assert [
        step.step_order
        for step in ordered_steps
    ] == [
        1,
        2,
        3,
        4,
    ]

    # =========================================================
    # 11. to_dict()
    # =========================================================

    data = section.to_dict()

    assert (
        data["SECTION_TITLE"]
        == "Nhân và chia hai lũy thừa cùng cơ số"
    )

    assert (
        data["SOURCE"]
        == "SGK"
    )

    assert (
        len(
            data["IMPLEMENTATION_STEPS"]
        )
        == 4
    )

    assert (
        data["TEACHER_CONCLUSION"]
        == section.teacher_conclusion
    )

    # =========================================================
    # 12. KHÔNG CHỨA LOGIC TEMPLATE
    # =========================================================

    forbidden_keys = {
        "COLUMN_1",
        "COLUMN_2",
        "COLUMN_TITLE",
        "TABLE_LAYOUT",
        "FONT",
        "ALIGNMENT",
    }

    assert forbidden_keys.isdisjoint(
        data.keys()
    )

    print("=" * 72)
    print(
        "LP-03G-ARCH - "
        "CONTENT SECTION TEST"
    )
    print("=" * 72)

    print("- ContentSection hợp lệ: PASS")
    print("- SECTION_TITLE rỗng bị chặn: PASS")
    print("- SECTION_ORDER = 0 bị chặn: PASS")
    print("- SOURCE sai bị chặn: PASS")
    print("- YCCD_IDS trùng bị chặn: PASS")
    print("- OBJECTIVE_IDS trùng bị chặn: PASS")
    print("- STEP_ID trùng bị chặn: PASS")
    print("- STEP_ORDER trùng bị chặn: PASS")
    print("- TEACHER_CONCLUSION rỗng bị chặn: PASS")
    print("- Sắp xếp ImplementationStep đúng: PASS")
    print("- to_dict() đúng: PASS")
    print("- Không chứa logic template: PASS")

    print(
        "\nKẾT QUẢ: 12/12 TEST PASS"
    )


if __name__ == "__main__":
    main()