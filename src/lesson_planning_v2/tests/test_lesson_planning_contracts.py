from dataclasses import FrozenInstanceError
import pytest
from lesson_planning_v2.models import LearningActivity, LessonObjective, LessonPlan, PeriodPlan, TeachingResource

def make_plan():
    o=LessonObjective("OBJ-001","KNOWLEDGE","Mục tiêu",("YCCD-MATH-06-0001",))
    r=TeachingResource("RES-001","Phiếu học tập","WORKSHEET")
    a=LearningActivity("ACT-001","Khám phá","LEARNING",1,("OBJ-001",),("RES-001",))
    p=PeriodPlan(1,(a,))
    return LessonPlan("LP-001","EP-001","ITEM-001","CTGDPT-2018-MATH",6,"Bài học","FULL_LESSON",1,
        curriculum_node_refs=("NODE-001",),canonical_requirement_refs=("YCCD-MATH-06-0001",),
        objectives=(o,),resources=(r,),periods=(p,))

def test_requirement_provenance(): assert make_plan().objectives[0].source_requirement_refs == ("YCCD-MATH-06-0001",)
def test_activity_objective_refs(): assert make_plan().periods[0].activities[0].objective_refs == ("OBJ-001",)
def test_activity_resource_refs(): assert make_plan().periods[0].activities[0].resource_refs == ("RES-001",)
def test_period_identity(): assert make_plan().periods[0].period_in_lesson == 1
def test_educational_plan_identity(): assert make_plan().educational_plan_id == "EP-001"
def test_plan_item_identity(): assert make_plan().plan_item_id == "ITEM-001"
def test_canonical_refs(): assert make_plan().canonical_requirement_refs == ("YCCD-MATH-06-0001",)
def test_full_lesson_mode(): assert make_plan().period_in_lesson is None
def test_frozen():
    with pytest.raises(FrozenInstanceError): make_plan().title = "Changed"
def test_no_presentation_fields():
    forbidden={"font","columns","column_headers","table_layout","margin","word_template","pdf_layout"}
    assert forbidden.isdisjoint(make_plan().__dataclass_fields__)
