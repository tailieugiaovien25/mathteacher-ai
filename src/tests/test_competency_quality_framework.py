import sys

sys.path.insert(0, "src")

from config.competency_quality_framework import (
    GENERAL_COMPETENCIES,
    MATHEMATICAL_COMPETENCIES,
    CORE_QUALITIES,
    ALL_COMPETENCIES,
    ALL_FRAMEWORK_ITEMS,
    get_framework_item,
    is_general_competency,
    is_mathematical_competency,
    is_core_quality,
)


def main() -> None:
    # =========================================================
    # 1. ĐÚNG SỐ LƯỢNG
    # =========================================================

    assert len(GENERAL_COMPETENCIES) == 3
    assert len(MATHEMATICAL_COMPETENCIES) == 5
    assert len(CORE_QUALITIES) == 5

    assert len(ALL_COMPETENCIES) == 8
    assert len(ALL_FRAMEWORK_ITEMS) == 13

    # =========================================================
    # 2. KHÔNG TRÙNG MÃ
    # =========================================================

    all_codes = (
        list(GENERAL_COMPETENCIES.keys())
        + list(MATHEMATICAL_COMPETENCIES.keys())
        + list(CORE_QUALITIES.keys())
    )

    assert len(all_codes) == len(set(all_codes))

    # =========================================================
    # 3. KIỂM TRA 3 NĂNG LỰC CHUNG
    # =========================================================

    assert (
        GENERAL_COMPETENCIES["NLC_TCTH"]
        == "Tự chủ và tự học"
    )

    assert (
        GENERAL_COMPETENCIES["NLC_GTHH"]
        == "Giao tiếp và hợp tác"
    )

    assert (
        GENERAL_COMPETENCIES["NLC_GQVDS"]
        == "Giải quyết vấn đề và sáng tạo"
    )

    # =========================================================
    # 4. KIỂM TRA 5 NĂNG LỰC TOÁN HỌC
    # =========================================================

    assert (
        MATHEMATICAL_COMPETENCIES["NLT_TDLL"]
        == "Tư duy và lập luận toán học"
    )

    assert (
        MATHEMATICAL_COMPETENCIES["NLT_MHH"]
        == "Mô hình hoá toán học"
    )

    assert (
        MATHEMATICAL_COMPETENCIES["NLT_GQVD"]
        == "Giải quyết vấn đề toán học"
    )

    assert (
        MATHEMATICAL_COMPETENCIES["NLT_GT"]
        == "Giao tiếp toán học"
    )

    assert (
        MATHEMATICAL_COMPETENCIES["NLT_CCPT"]
        == "Sử dụng công cụ, phương tiện học toán"
    )

    # =========================================================
    # 5. KIỂM TRA 5 PHẨM CHẤT
    # =========================================================

    assert (
        CORE_QUALITIES["PC_YN"]
        == "Yêu nước"
    )

    assert (
        CORE_QUALITIES["PC_NA"]
        == "Nhân ái"
    )

    assert (
        CORE_QUALITIES["PC_CC"]
        == "Chăm chỉ"
    )

    assert (
        CORE_QUALITIES["PC_TT"]
        == "Trung thực"
    )

    assert (
        CORE_QUALITIES["PC_TN"]
        == "Trách nhiệm"
    )

    # =========================================================
    # 6. HÀM TRA CỨU
    # =========================================================

    assert (
        get_framework_item("nlt_tdll")
        == "Tư duy và lập luận toán học"
    )

    assert (
        get_framework_item("pc_cc")
        == "Chăm chỉ"
    )

    # =========================================================
    # 7. PHÂN LOẠI MÃ
    # =========================================================

    assert is_general_competency(
        "NLC_TCTH"
    )

    assert not is_general_competency(
        "NLT_TDLL"
    )

    assert is_mathematical_competency(
        "NLT_TDLL"
    )

    assert not is_mathematical_competency(
        "PC_CC"
    )

    assert is_core_quality(
        "PC_CC"
    )

    assert not is_core_quality(
        "NLC_GTHH"
    )

    # =========================================================
    # 8. MÃ KHÔNG TỒN TẠI
    # =========================================================

    unknown_blocked = False

    try:
        get_framework_item(
            "UNKNOWN_CODE"
        )
    except KeyError:
        unknown_blocked = True

    assert unknown_blocked

    print("=" * 72)
    print(
        "LP-03F.3 - "
        "COMPETENCY & QUALITY FRAMEWORK TEST"
    )
    print("=" * 72)

    print("- 3 năng lực chung: PASS")
    print("- 5 năng lực toán học: PASS")
    print("- 5 phẩm chất: PASS")
    print("- Tổng 13 mục framework: PASS")
    print("- Không trùng mã: PASS")
    print("- Nội dung mã chuẩn: PASS")
    print("- Tra cứu framework: PASS")
    print("- Phân loại mã đúng: PASS")
    print("- Mã không tồn tại bị chặn: PASS")

    print(
        "\nKẾT QUẢ: 9/9 TEST PASS"
    )


if __name__ == "__main__":
    main()