from document_standardization import (
    LessonPlanDocumentContextApplier,
)


def replace_heading(text, title="Đơn thức"):
    return (
        LessonPlanDocumentContextApplier
        ._replace_lesson_heading(
            text,
            lesson_title=title,
        )
    )


def test_heading_with_bai_number():
    result = replace_heading(
        "Tiết 1. BÀI 1. BÀI CŨ"
    )

    assert result == (
        "Tiết 1. BÀI 1. Đơn thức"
    )


def test_heading_with_section_symbol():
    result = replace_heading(
        "TIẾT 4 - §4: PHÉP CỘNG VÀ PHÉP TRỪ SỐ TỰ NHIÊN"
    )

    assert result == (
        "TIẾT 4 - §4: Đơn thức"
    )


def test_heading_with_bai_colon():
    result = replace_heading(
        "TIẾT 4 - BÀI 4: BÀI CŨ"
    )

    assert result == (
        "TIẾT 4 - BÀI 4: Đơn thức"
    )


def test_heading_with_multiple_periods():
    result = replace_heading(
        "Tiết 4,5. Bài 3. BÀI CŨ (2 tiết)"
    )

    assert result == (
        "Tiết 4,5. Bài 3. Đơn thức (2 tiết)"
    )


def test_heading_without_lesson_marker_is_ignored():
    result = replace_heading(
        "Tiết 4 - Kiểm tra bài cũ"
    )

    assert result is None


def test_normal_content_is_ignored():
    result = replace_heading(
        "Hoạt động 1: Giáo viên giao nhiệm vụ."
    )

    assert result is None
