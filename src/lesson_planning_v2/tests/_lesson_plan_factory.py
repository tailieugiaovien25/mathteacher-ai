from lesson_planning_v2.models import (
    LearningActivity,
    LessonObjective,
    LessonPlan,
    PeriodPlan,
    TeachingResource,
)


def make_valid_plan(**overrides):
    objective = LessonObjective(
        objective_id="OBJ-001",
        objective_type="KNOWLEDGE",
        statement="Mục tiêu",
        source_requirement_refs=("YCCD-MATH-06-0001",),
    )
    resource = TeachingResource(
        resource_id="RES-001",
        name="Phiếu học tập",
        resource_type="WORKSHEET",
    )
    activity = LearningActivity(
        activity_id="ACT-001",
        title="Khám phá",
        activity_type="LEARNING",
        order=1,
        objective_refs=("OBJ-001",),
        resource_refs=("RES-001",),
    )
    values = dict(
        lesson_plan_id="LP-001",
        educational_plan_id="EP-001",
        plan_item_id="ITEM-001",
        curriculum_ref="CTGDPT-2018-MATH",
        grade=6,
        title="Bài học",
        plan_mode="FULL_LESSON",
        total_periods=1,
        canonical_requirement_refs=("YCCD-MATH-06-0001",),
        objectives=(objective,),
        resources=(resource,),
        periods=(PeriodPlan(1, (activity,)),),
    )
    values.update(overrides)
    return LessonPlan(**values)
