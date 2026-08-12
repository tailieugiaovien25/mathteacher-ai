from dataclasses import dataclass, field
from typing import Any

from educational_planning_v2.models.curriculum_scope import CurriculumScope


@dataclass(frozen=True)
class EducationalPlanItem:
    """One teachable/schedulable item in an educational plan."""

    plan_item_id: str
    title: str
    curriculum_scope: CurriculumScope

    periods: int
    sequence: int = 0

    planned_time: str | None = None
    teaching_equipment: tuple[str, ...] = ()
    teaching_location: str | None = None

    status: str = "DRAFT"
    metadata: dict[str, Any] = field(default_factory=dict)
