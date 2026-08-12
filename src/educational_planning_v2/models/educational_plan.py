from dataclasses import dataclass, field
from typing import Any

from educational_planning_v2.models.plan_item import EducationalPlanItem


@dataclass(frozen=True)
class EducationalPlan:
    """Domain contract for a teacher/subject educational plan."""

    educational_plan_id: str
    academic_year: str
    subject: str
    grade: int

    items: tuple[EducationalPlanItem, ...] = ()

    status: str = "DRAFT"
    metadata: dict[str, Any] = field(default_factory=dict)
