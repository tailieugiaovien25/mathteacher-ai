from lesson_planning_v2.services.lesson_plan_preferred_filename_policy import preferred_filename
from lesson_planning_v2.services.lesson_plan_smart_up_resolver import SmartUpContext,SmartUpDocument,resolve_documents

def d(name,title=""):
    return SmartUpDocument(file_name=name,storage_provider="GOOGLE_DRIVE",storage_file_id=name,title=title)

def test_week_name():
    assert preferred_filename(code="ANH",grade=6,week_number=1).filename=="KHBD.ANH6.TUAN01.docx"

def test_period_name():
    assert preferred_filename(code="TSH",grade=6,curriculum_period=1).filename=="KHBD.TSH6.001.docx"

def test_preferred_beats_legacy():
    c=SmartUpContext(expected_file_name="6GA001W01.docx",preferred_file_name="KHBD.ANH6.TUAN01.docx",week_number=1)
    r=resolve_documents([d("6GA001W01.docx"),d("KHBD.ANH6.TUAN1.docx")],c)
    assert r.status=="FOUND"
    assert r.best.document.file_name=="KHBD.ANH6.TUAN1.docx"

def test_generic_metadata_is_not_enough_for_week():
    c=SmartUpContext(expected_file_name="legacy.docx",preferred_file_name="KHBD.ANH6.TUAN01.docx",subject_ref="A",grade="6",week_number=1,lesson_title="Unit 1")
    assert resolve_documents([d("x.docx","English 6 Unit 9"),d("y.docx","English 6 Unit 5")],c).status=="NOT_FOUND"

def test_week_metadata_can_fallback():
    c=SmartUpContext(expected_file_name="legacy.docx",preferred_file_name="KHBD.ANH6.TUAN01.docx",week_number=1)
    assert resolve_documents([d("old.docx","English 6 tuan01")],c).status=="FOUND"
