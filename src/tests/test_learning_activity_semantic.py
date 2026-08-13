import sys

sys.path.insert(0, "src")

from models.content_section import ContentSection
from models.implementation_step import ImplementationStep
from models.learning_activity import LearningActivity


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


def make_steps(
    prefix: str,
) -> list[ImplementationStep]:
    return [
        ImplementationStep(
            step_id=f"{prefix}_STEP01",
            step_order=1,
            step_type="CHUYEN_GIAO",
            teacher_action=(
                "Giáo viên giao nhiệm vụ."
            ),
            student_action=(
                "Học sinh tiếp nhận nhiệm vụ."
            ),
            expected_result=(
                "Học sinh hiểu yêu cầu."
            ),
        ),
        ImplementationStep(
            step_id=f"{prefix}_STEP02",
            step_order=2,
            step_type="THUC_HIEN",
            teacher_action=(
                "Giáo viên quan sát và hỗ trợ."
            ),
            student_action=(
                "Học sinh thực hiện nhiệm vụ."
            ),
            expected_result=(
                "Học sinh hoàn thành nhiệm vụ."
            ),
        ),
    ]


def make_section(
    section_id: str,
    section_order: int,
    title: str,
) -> ContentSection:
    return ContentSection(
        section_id=section_id,
        lesson_key="T7_DAI_B03",
        section_order=section_order,
        section_title=title,
        source="SGK",
        yccd_ids=[
            "T7_DAI_B03_Y02",
        ],
        objective_ids=[
            "T7_DAI_B03_OBJ_KT02",
        ],
        objective_text=(
            "Mô tả và thực hiện được phép tính "
            "với lũy thừa."
        ),
        content=(
            "Nội dung của đề mục."
        ),
        expected_product=(
            "Học sinh hoàn thành nhiệm vụ "
            "và nêu được kiến thức."
        ),
        implementation_steps=make_steps(
            section_id
        ),
        teacher_conclusion=(
            "Giáo viên chốt kiến thức của đề mục."
        ),
        status="draft",
    )


def main() -> None:
    # =========================================================
    # 1. MO_DAU SEMANTIC HỢP LỆ
    # =========================================================

    opening = LearningActivity(
        activity_id="T7_DAI_B03_P01_ACT01",
        lesson_key="T7_DAI_B03",
        period_in_lesson=1,
        activity_type="MO_DAU",
        title="Đặt vấn đề",
        objective_ids=[
            "T7_DAI_B03_OBJ_KT01",
        ],
        yccd_ids=[
            "T7_DAI_B03_Y01",
        ],
        objective_text=(
            "Gợi nhớ kiến thức liên quan "
            "và xác định vấn đề cần tìm hiểu."
        ),
        content=(
            "Tình huống mở đầu."
        ),
        expected_product=(
            "Học sinh xác định được vấn đề "
            "cần giải quyết."
        ),
        implementation_steps=make_steps(
            "OPENING"
        ),
        resource_ids=[
            "RES_IMAGE_001",
        ],
        teacher_conclusion=(
            "Giáo viên chốt vấn đề "
            "cần tìm hiểu trong tiết học."
        ),
        order=1,
        status="draft",
    )

    opening.validate()

    # =========================================================
    # 2. HÌNH THÀNH KIẾN THỨC CÓ CONTENT SECTION
    # =========================================================

    knowledge = LearningActivity(
        activity_id="T7_DAI_B03_P02_ACT02",
        lesson_key="T7_DAI_B03",
        period_in_lesson=2,
        activity_type="HINH_THANH_KIEN_THUC",
        title="Hình thành kiến thức",
        objective_ids=[
            "T7_DAI_B03_OBJ_KT02",
        ],
        yccd_ids=[
            "T7_DAI_B03_Y02",
        ],
        objective_text=(
            "Hình thành các quy tắc "
            "về lũy thừa."
        ),
        content=(
            "Các đề mục kiến thức theo SGK."
        ),
        expected_product=(
            "Học sinh nêu và vận dụng "
            "được các quy tắc."
        ),
        implementation_steps=[],
        content_sections=[
            make_section(
                "T7_DAI_B03_S01",
                1,
                "Nhân hai lũy thừa cùng cơ số",
            ),
            make_section(
                "T7_DAI_B03_S02",
                2,
                "Chia hai lũy thừa cùng cơ số",
            ),
        ],
        teacher_conclusion=(
            "Giáo viên hệ thống lại "
            "các kiến thức vừa hình thành."
        ),
        order=2,
        status="draft",
    )

    knowledge.validate()

    # =========================================================
    # 3. LUYỆN TẬP KHÔNG CẦN CONTENT SECTION
    # =========================================================

    practice = LearningActivity(
        activity_id="T7_DAI_B03_P02_ACT03",
        lesson_key="T7_DAI_B03",
        period_in_lesson=2,
        activity_type="LUYEN_TAP",
        title="Luyện tập",
        objective_text=(
            "Củng cố kiến thức đã học."
        ),
        content=(
            "Bài tập luyện tập."
        ),
        expected_product=(
            "Học sinh hoàn thành bài tập."
        ),
        implementation_steps=make_steps(
            "PRACTICE"
        ),
        teacher_conclusion=(
            "Giáo viên chốt phương pháp "
            "và lỗi cần tránh."
        ),
        order=3,
    )

    practice.validate()

    # =========================================================
    # 4. RESOURCE_IDS TRÙNG
    # =========================================================

    expect_value_error(
        LearningActivity(
            activity_id="TEST_RESOURCE_DUP",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            activity_type="MO_DAU",
            title="Mở đầu",
            resource_ids=[
                "RES01",
                "RES01",
            ],
            teacher_conclusion="Chốt.",
        )
    )

    # =========================================================
    # 5. STEP_ID TRÙNG
    # =========================================================

    duplicate_steps = make_steps(
        "DUP"
    )

    duplicate_steps.append(
        ImplementationStep(
            step_id="DUP_STEP01",
            step_order=3,
            step_type="KHAC",
            note="Trùng STEP_ID.",
        )
    )

    expect_value_error(
        LearningActivity(
            activity_id="TEST_STEP_DUP",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            activity_type="LUYEN_TAP",
            title="Luyện tập",
            implementation_steps=(
                duplicate_steps
            ),
            teacher_conclusion="Chốt.",
        )
    )

    # =========================================================
    # 6. STEP_ORDER TRÙNG
    # =========================================================

    duplicate_order = make_steps(
        "ORDER"
    )

    duplicate_order.append(
        ImplementationStep(
            step_id="ORDER_STEP03",
            step_order=2,
            step_type="KHAC",
            note="Trùng STEP_ORDER.",
        )
    )

    expect_value_error(
        LearningActivity(
            activity_id="TEST_STEP_ORDER",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            activity_type="LUYEN_TAP",
            title="Luyện tập",
            implementation_steps=(
                duplicate_order
            ),
            teacher_conclusion="Chốt.",
        )
    )

    # =========================================================
    # 7. SECTION_ID TRÙNG
    # =========================================================

    section_a = make_section(
        "SEC_DUP",
        1,
        "Đề mục 1",
    )

    section_b = make_section(
        "SEC_DUP",
        2,
        "Đề mục 2",
    )

    expect_value_error(
        LearningActivity(
            activity_id="TEST_SECTION_ID",
            lesson_key="T7_DAI_B03",
            period_in_lesson=2,
            activity_type="HINH_THANH_KIEN_THUC",
            title="Hình thành kiến thức",
            content_sections=[
                section_a,
                section_b,
            ],
            teacher_conclusion="Chốt.",
        )
    )

    # =========================================================
    # 8. SECTION_ORDER TRÙNG
    # =========================================================

    section_c = make_section(
        "SEC01",
        1,
        "Đề mục 1",
    )

    section_d = make_section(
        "SEC02",
        1,
        "Đề mục 2",
    )

    expect_value_error(
        LearningActivity(
            activity_id="TEST_SECTION_ORDER",
            lesson_key="T7_DAI_B03",
            period_in_lesson=2,
            activity_type="HINH_THANH_KIEN_THUC",
            title="Hình thành kiến thức",
            content_sections=[
                section_c,
                section_d,
            ],
            teacher_conclusion="Chốt.",
        )
    )

    # =========================================================
    # 9. SECTION KHÁC LESSON_KEY
    # =========================================================

    wrong_section = ContentSection(
        section_id="WRONG_KEY",
        lesson_key="T7_DAI_B04",
        section_order=1,
        section_title="Đề mục",
        teacher_conclusion="Chốt.",
    )

    expect_value_error(
        LearningActivity(
            activity_id="TEST_SECTION_KEY",
            lesson_key="T7_DAI_B03",
            period_in_lesson=2,
            activity_type="HINH_THANH_KIEN_THUC",
            title="Hình thành kiến thức",
            content_sections=[
                wrong_section,
            ],
            teacher_conclusion="Chốt.",
        )
    )

    # =========================================================
    # 10. TEACHER_CONCLUSION RỖNG
    # =========================================================

    expect_value_error(
        LearningActivity(
            activity_id="TEST_NO_CONCLUSION",
            lesson_key="T7_DAI_B03",
            period_in_lesson=1,
            activity_type="MO_DAU",
            title="Mở đầu",
            teacher_conclusion="",
        )
    )

    # =========================================================
    # 11. SẮP XẾP SECTION
    # =========================================================

    ordered_sections = (
        knowledge.get_content_sections()
    )

    assert [
        section.section_order
        for section in ordered_sections
    ] == [1, 2]

    # =========================================================
    # 12. to_dict()
    # =========================================================

    data = knowledge.to_dict()

    assert (
        data["ACTIVITY_TYPE"]
        == "HINH_THANH_KIEN_THUC"
    )

    assert (
        len(
            data["CONTENT_SECTIONS"]
        )
        == 2
    )

    assert (
        data["CONTENT_SECTIONS"][0][
            "SECTION_TITLE"
        ]
        == "Nhân hai lũy thừa cùng cơ số"
    )

    assert (
        data["TEACHER_CONCLUSION"]
        == knowledge.teacher_conclusion
    )

    # =========================================================
    # 13. RESOURCE IDS ĐƯỢC GIỮ
    # =========================================================

    opening_data = opening.to_dict()

    assert (
        opening_data["RESOURCE_IDS"]
        == ["RES_IMAGE_001"]
    )

    # =========================================================
    # 14. KHÔNG CHỨA LOGIC TEMPLATE
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
        "LEARNING ACTIVITY SEMANTIC TEST"
    )
    print("=" * 72)

    print("- MO_DAU semantic hợp lệ: PASS")
    print("- HINH_THANH_KIEN_THUC có section: PASS")
    print("- LUYEN_TAP không cần section: PASS")
    print("- RESOURCE_IDS trùng bị chặn: PASS")
    print("- STEP_ID trùng bị chặn: PASS")
    print("- STEP_ORDER trùng bị chặn: PASS")
    print("- SECTION_ID trùng bị chặn: PASS")
    print("- SECTION_ORDER trùng bị chặn: PASS")
    print("- Section khác LESSON_KEY bị chặn: PASS")
    print("- TEACHER_CONCLUSION rỗng bị chặn: PASS")
    print("- Sắp xếp ContentSection đúng: PASS")
    print("- to_dict() semantic đúng: PASS")
    print("- RESOURCE_IDS được giữ: PASS")
    print("- Không chứa logic template: PASS")

    print(
        "\nKẾT QUẢ: 14/14 TEST PASS"
    )


if __name__ == "__main__":
    main()