from dataclasses import dataclass, field
from typing import Any
from lesson_planning_v2.models.learning_activity import LearningActivity

@dataclass(frozen=True)
class PeriodPlan:
    period_in_lesson: int
    activities: tuple[LearningActivity, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
