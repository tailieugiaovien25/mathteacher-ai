from document_intelligence.lesson_plan_recognition import (
    LessonPlanRecognitionEngine,
)


def recognize(text):
    return LessonPlanRecognitionEngine().recognize_text(
        text
    )


def values(text):
    return {
        item.field_name: item.value
        for item in recognize(text)
    }


def test_recognizes_dates_and_class():
    result = values(
        "Ngày soạn: 07/09/2026 "
        "Ngày dạy: 08/09/2026 "
        "Lớp: 8A2"
    )

    assert result["drafting_date"] == "07/09/2026"
    assert result["teaching_date"] == "08/09/2026"
    assert result["class_name"] == "8A2"


def test_recognizes_explicit_period():
    result = values(
        "Tiết PPCT: 12"
    )

    assert result["curriculum_period"] == "12"


def test_recognizes_explicit_title():
    result = values(
        "Tên bài: Đơn thức"
    )

    assert result["lesson_title"] == "Đơn thức"


def test_recognizes_bai_heading():
    result = values(
        "Tiết 4. Bài 3. Đơn thức"
    )

    assert result["curriculum_period"] == "4"
    assert result["lesson_title"] == "Đơn thức"


def test_recognizes_section_heading():
    result = values(
        "TIẾT 4 - §4: PHÉP CỘNG VÀ PHÉP TRỪ SỐ TỰ NHIÊN"
    )

    assert result["curriculum_period"] == "4"
    assert (
        result["lesson_title"]
        == "PHÉP CỘNG VÀ PHÉP TRỪ SỐ TỰ NHIÊN"
    )


def test_recognizes_multiple_period_heading():
    result = values(
        "Tiết 4,5. Bài 3. Đơn thức (2 tiết)"
    )

    assert result["curriculum_period"] == "5"
    assert result["lesson_title"] == "Đơn thức"


def test_normal_content_is_not_recognized():
    result = recognize(
        "Hoạt động 1: Giáo viên giao nhiệm vụ."
    )

    assert result == ()
