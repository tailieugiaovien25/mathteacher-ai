from portal_v2.context.canonical_code_catalog import DEFAULT_CANONICAL_CODES
from portal_v2.context.canonical_code_service import (
 CanonicalCodeService, InMemoryCanonicalCodeRepository,
 CanonicalDocumentRecord, CanonicalLessonPlanFileResolver,
)

def repo():
 return InMemoryCanonicalCodeRepository(DEFAULT_CANONICAL_CODES.values())

def test_admin_can_add_and_deactivate_code_without_core_change():
 s=CanonicalCodeService(repo())
 x=s.upsert_code(namespace="component",code="HH",label="Hóa học")
 assert x.code=="HH"
 assert s.set_active(namespace="component",code="HH",active=False).active is False

def test_resolve_grade7_math_algebra_003():
 s=CanonicalCodeService(repo())
 r=s.resolve_lesson_plan(grade=7,ppct_position=3,subject_code="T",component_code="TDS",lesson_plan_code="GTDS")
 assert r.curriculum_business_id=="7TDS003"
 assert r.lesson_plan_business_id=="7GTDS003"
 assert r.exact_filename=="7GTDS003.docx"

def test_inactive_code_cannot_generate_new_identity():
 s=CanonicalCodeService(repo())
 s.set_active(namespace="component",code="TDS",active=False)
 try:
  s.resolve_lesson_plan(grade=7,ppct_position=3,subject_code="T",component_code="TDS",lesson_plan_code="GTDS")
 except KeyError:
  pass
 else:
  raise AssertionError("inactive code accepted")

def test_file_resolver_requires_exact_filename_and_business_id():
 f=CanonicalLessonPlanFileResolver()
 good=CanonicalDocumentRecord("uuid-1","7GTDS003","7GTDS003.docx","storage/a")
 bad=CanonicalDocumentRecord("uuid-2","7GTDS003","7GTDS003-old.docx","storage/b")
 assert f.resolve_exact(expected_business_id="7GTDS003",expected_filename="7GTDS003.docx",records=[bad,good])==good

def test_file_resolver_rejects_duplicate_exact_records():
 f=CanonicalLessonPlanFileResolver()
 rows=[
  CanonicalDocumentRecord("1","7GTDS003","7GTDS003.docx","a"),
  CanonicalDocumentRecord("2","7GTDS003","7GTDS003.docx","b"),
 ]
 try:
  f.resolve_exact(expected_business_id="7GTDS003",expected_filename="7GTDS003.docx",records=rows)
 except ValueError:
  pass
 else:
  raise AssertionError("duplicate exact files accepted")
