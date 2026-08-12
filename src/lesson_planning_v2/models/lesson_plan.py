from dataclasses import dataclass, field
from typing import Any
from lesson_planning_v2.models.lesson_objective import LessonObjective
from lesson_planning_v2.models.period_plan import PeriodPlan
from lesson_planning_v2.models.teaching_resource import TeachingResource

@dataclass(frozen=True)
class LessonPlan:
    lesson_plan_id: str
    educational_plan_id: str
    plan_item_id: str
    curriculum_ref: str
    grade: int
    title: str
    plan_mode: str
    total_periods: int
    period_in_lesson: int | None = None
    curriculum_node_refs: tuple[str, ...] = ()
    canonical_requirement_refs: tuple[str, ...] = ()
    objectives: tuple[LessonObjective, ...] = ()
    resources: tuple[TeachingResource, ...] = ()
    periods: tuple[PeriodPlan, ...] = ()
    status: str = "DRAFT"
    metadata: dict[str, Any] = field(default_factory=dict)
