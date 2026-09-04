from document_standardization.lesson_plan_document_context_applier import (
    LessonPlanDocumentContextApplier,
)


def replace(text, field_name, value):
    return LessonPlanDocumentContextApplier._replace_field_in_text(
        text,
        field_name=field_name,
        value=value,
        context=None,
    )


def test_replaces_english_planning_placeholder():
    assert replace("Date of planning:…………..", "drafting_date", "11/09/2026") == (
        "Date of planning:11/09/2026"
    )


def test_replaces_english_teaching_placeholder():
    assert replace("Date of teaching: ………..…", "teaching_date", "14/09/2026") == (
        "Date of teaching: 14/09/2026"
    )


def test_replaces_english_period_heading():
    assert LessonPlanDocumentContextApplier._replace_period_heading(
        "Period 9 : UNIT 2: MY HOUSE",
        curriculum_period=10,
        period_in_lesson=1,
    ) == "Period 10 : UNIT 2: MY HOUSE"


def test_preserves_vietnamese_date_replacement():
    assert replace("Ngày soạn: 01/09/2026", "drafting_date", "11/09/2026") == (
        "Ngày soạn: 11/09/2026"
    )
