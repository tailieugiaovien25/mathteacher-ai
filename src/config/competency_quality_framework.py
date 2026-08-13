GENERAL_COMPETENCIES = {
    "NLC_TCTH": "Tự chủ và tự học",
    "NLC_GTHH": "Giao tiếp và hợp tác",
    "NLC_GQVDS": "Giải quyết vấn đề và sáng tạo",
}


MATHEMATICAL_COMPETENCIES = {
    "NLT_TDLL": "Tư duy và lập luận toán học",
    "NLT_MHH": "Mô hình hoá toán học",
    "NLT_GQVD": "Giải quyết vấn đề toán học",
    "NLT_GT": "Giao tiếp toán học",
    "NLT_CCPT": "Sử dụng công cụ, phương tiện học toán",
}


CORE_QUALITIES = {
    "PC_YN": "Yêu nước",
    "PC_NA": "Nhân ái",
    "PC_CC": "Chăm chỉ",
    "PC_TT": "Trung thực",
    "PC_TN": "Trách nhiệm",
}


ALL_COMPETENCIES = {
    **GENERAL_COMPETENCIES,
    **MATHEMATICAL_COMPETENCIES,
}


ALL_FRAMEWORK_ITEMS = {
    **GENERAL_COMPETENCIES,
    **MATHEMATICAL_COMPETENCIES,
    **CORE_QUALITIES,
}


def get_framework_item(
    code: str,
) -> str:
    """
    Trả về tên chuẩn theo mã framework.
    """

    normalized_code = (
        str(code)
        .strip()
        .upper()
    )

    if normalized_code not in ALL_FRAMEWORK_ITEMS:
        raise KeyError(
            f"Mã framework không tồn tại: {code}"
        )

    return ALL_FRAMEWORK_ITEMS[
        normalized_code
    ]


def is_general_competency(
    code: str,
) -> bool:
    return (
        str(code)
        .strip()
        .upper()
        in GENERAL_COMPETENCIES
    )


def is_mathematical_competency(
    code: str,
) -> bool:
    return (
        str(code)
        .strip()
        .upper()
        in MATHEMATICAL_COMPETENCIES
    )


def is_core_quality(
    code: str,
) -> bool:
    return (
        str(code)
        .strip()
        .upper()
        in CORE_QUALITIES
    )