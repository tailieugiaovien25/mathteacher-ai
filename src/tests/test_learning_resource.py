import sys

sys.path.insert(0, "src")

from models.learning_resource import LearningResource


def expect_value_error(
    resource: LearningResource,
) -> None:
    try:
        resource.validate()
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError but validation passed."
    )


def main() -> None:
    # =========================================================
    # 1. THIẾT BỊ HỢP LỆ
    # =========================================================

    equipment = LearningResource(
        resource_id="RES_EQUIPMENT_001",
        resource_type="EQUIPMENT",
        title="Thước thẳng và compa",
        description=(
            "Dụng cụ hỗ trợ hoạt động hình học."
        ),
        source_type="LOCAL",
        pedagogical_purpose=(
            "Hỗ trợ học sinh dựng và quan sát hình."
        ),
    )

    equipment.validate()

    # =========================================================
    # 2. HÌNH HỌC ĐƯỢC TẠO BỞI HỆ THỐNG
    # =========================================================

    geometry = LearningResource(
        resource_id="RES_GEOMETRY_001",
        resource_type="GEOMETRY_FIGURE",
        title="Hình tam giác ABC có MN song song BC",
        description=(
            "Hình minh họa phục vụ nội dung "
            "về tam giác đồng dạng."
        ),
        source_type="GENERATED",
        source_reference=(
            "geometry-engine://figure-001"
        ),
        pedagogical_purpose=(
            "Giúp học sinh quan sát các yếu tố "
            "và quan hệ hình học."
        ),
        alt_text=(
            "Tam giác ABC, M thuộc AB, N thuộc AC "
            "và MN song song BC."
        ),
    )

    geometry.validate()

    # =========================================================
    # 3. ẢNH THỰC TẾ TỪ WEB
    # =========================================================

    web_image = LearningResource(
        resource_id="RES_IMAGE_WEB_001",
        resource_type="IMAGE",
        title="Hình ảnh thực tế dùng cho mở đầu",
        description=(
            "Ảnh thực tế tạo tình huống học tập."
        ),
        source_type="WEB",
        source_reference=(
            "https://example.org/example-image"
        ),
        pedagogical_purpose=(
            "Tạo tình huống mở đầu và kết nối "
            "kiến thức với thực tiễn."
        ),
        alt_text=(
            "Hình ảnh thực tế liên quan đến "
            "nội dung bài học."
        ),
        license_info=(
            "Thông tin giấy phép sẽ được "
            "Resource Manager quản lý."
        ),
    )

    web_image.validate()

    # =========================================================
    # 4. FILE GIÁO VIÊN TẢI LÊN
    # =========================================================

    teacher_document = LearningResource(
        resource_id="RES_DOC_001",
        resource_type="DOCUMENT",
        title="Phiếu học tập số 1",
        description=(
            "Phiếu học tập do giáo viên cung cấp."
        ),
        source_type="TEACHER_UPLOAD",
        source_reference=(
            "teacher-upload://worksheet-001"
        ),
        pedagogical_purpose=(
            "Dùng trong hoạt động luyện tập."
        ),
    )

    teacher_document.validate()

    # =========================================================
    # 5. RESOURCE_ID RỖNG
    # =========================================================

    expect_value_error(
        LearningResource(
            resource_id="",
            resource_type="IMAGE",
            title="Ảnh minh họa",
        )
    )

    # =========================================================
    # 6. RESOURCE_TYPE SAI
    # =========================================================

    expect_value_error(
        LearningResource(
            resource_id="RES_BAD_TYPE",
            resource_type="VIDEO_3D_UNKNOWN",
            title="Tài nguyên",
        )
    )

    # =========================================================
    # 7. TITLE RỖNG
    # =========================================================

    expect_value_error(
        LearningResource(
            resource_id="RES_NO_TITLE",
            resource_type="DOCUMENT",
            title="",
        )
    )

    # =========================================================
    # 8. SOURCE_TYPE SAI
    # =========================================================

    expect_value_error(
        LearningResource(
            resource_id="RES_BAD_SOURCE",
            resource_type="IMAGE",
            title="Ảnh minh họa",
            source_type="UNKNOWN_SOURCE",
        )
    )

    # =========================================================
    # 9. WEB THIẾU SOURCE_REFERENCE
    # =========================================================

    expect_value_error(
        LearningResource(
            resource_id="RES_WEB_NO_SOURCE",
            resource_type="IMAGE",
            title="Ảnh trên mạng",
            source_type="WEB",
            source_reference="",
        )
    )

    # =========================================================
    # 10. is_visual
    # =========================================================

    assert geometry.is_visual is True
    assert web_image.is_visual is True
    assert equipment.is_visual is False
    assert teacher_document.is_visual is False

    # =========================================================
    # 11. to_dict()
    # =========================================================

    data = geometry.to_dict()

    assert (
        data["RESOURCE_TYPE"]
        == "GEOMETRY_FIGURE"
    )

    assert (
        data["SOURCE_TYPE"]
        == "GENERATED"
    )

    assert (
        data["ALT_TEXT"]
        == geometry.alt_text
    )

    # =========================================================
    # 12. KHÔNG CHỨA LOGIC TEMPLATE
    # =========================================================

    forbidden_keys = {
        "COLUMN_1",
        "COLUMN_2",
        "COLUMN_TITLE",
        "TABLE_LAYOUT",
        "WIDTH",
        "HEIGHT",
        "ALIGNMENT",
        "FONT",
    }

    assert forbidden_keys.isdisjoint(
        data.keys()
    )

    print("=" * 72)
    print(
        "LP-03G-ARCH - "
        "LEARNING RESOURCE TEST"
    )
    print("=" * 72)

    print("- EQUIPMENT hợp lệ: PASS")
    print("- GEOMETRY_FIGURE generated hợp lệ: PASS")
    print("- IMAGE nguồn WEB hợp lệ: PASS")
    print("- DOCUMENT giáo viên tải lên hợp lệ: PASS")
    print("- RESOURCE_ID rỗng bị chặn: PASS")
    print("- RESOURCE_TYPE sai bị chặn: PASS")
    print("- TITLE rỗng bị chặn: PASS")
    print("- SOURCE_TYPE sai bị chặn: PASS")
    print("- WEB thiếu SOURCE_REFERENCE bị chặn: PASS")
    print("- is_visual phân loại đúng: PASS")
    print("- to_dict() semantic đúng: PASS")
    print("- Không chứa logic template: PASS")

    print(
        "\nKẾT QUẢ: 12/12 TEST PASS"
    )


if __name__ == "__main__":
    main()