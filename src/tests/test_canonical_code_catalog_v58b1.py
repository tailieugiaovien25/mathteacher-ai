from portal_v2.context.canonical_code_catalog import *
def test_grade7_math_algebra_003():
 i=CanonicalEducationalInputIdentity(7,3,"T","TDS","GTDS")
 assert i.subject_business_id=="7T"
 assert i.curriculum_business_id=="7TDS003"
 assert i.lesson_plan_business_id=="7GTDS003"
 assert i.lesson_plan_filename=="7GTDS003.docx"
 assert i.equipment_group_business_id=="7TB003"
 assert i.equipment_item_business_id(1)=="7TB003-01"
def test_exact_filename():
 i=CanonicalEducationalInputIdentity(7,3,"T","TDS","GTDS")
 assert exact_lesson_plan_filename(i)=="7GTDS003.docx"
def test_mutable_names_not_identity():
 assert "lesson_title" not in CanonicalEducationalInputIdentity.__dataclass_fields__
def test_locked_codes():
 assert DEFAULT_CANONICAL_CODES["subject.math"].code=="T"
 assert DEFAULT_CANONICAL_CODES["lesson_plan.math.algebra"].code=="GTDS"
 assert DEFAULT_CANONICAL_CODES["lesson_plan.english"].code=="GTA"
 assert DEFAULT_CANONICAL_CODES["equipment"].code=="TB"
