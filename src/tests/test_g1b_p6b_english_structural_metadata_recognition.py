from docx import Document
from document_standardization.lesson_plan_metadata_locator import LessonPlanMetadataLocator, MetadataField

def _fields(text):
    document = Document()
    document.add_paragraph(text)
    return {x.field: x.value_text for x in LessonPlanMetadataLocator().locate(document)}

def test_p6b_date_of_planning_is_drafting_date():
    assert _fields("Date of planning: 6/9/2025")[MetadataField.DRAFTING_DATE] == "6/9/2025"

def test_p6b_date_of_teaching_with_class():
    values = _fields("Date of teaching 6A1: 09/9/2025")
    assert values[MetadataField.TEACHING_DATE] == "09/9/2025"
    assert values[MetadataField.CLASS_NAME] == "6A1"

def test_p6b_real_compact_header_extracts_expected_fields():
    values = _fields("6A2: 09/9/2025Period 1INTRODUCE HOW TO LEARN.")
    assert values[MetadataField.CLASS_NAME] == "6A2"
    assert values[MetadataField.TEACHING_DATE] == "09/9/2025"
    assert values[MetadataField.CURRICULUM_PERIOD] == "1"
    assert values[MetadataField.LESSON_TITLE] == "INTRODUCE HOW TO LEARN."

def test_p6b_ambiguous_body_words_are_not_metadata():
    samples = ("After the lesson, ss will be to:", "3. New lesson",
               "The components of each unit", "105 periods /37 weeks.",
               "1.In class: to study seriously.")
    for sample in samples:
        assert _fields(sample) == {}

def test_p6b_vietnamese_compatibility_remains():
    assert _fields("Ngay soan: 6/9/2025")[MetadataField.DRAFTING_DATE] == "6/9/2025"
