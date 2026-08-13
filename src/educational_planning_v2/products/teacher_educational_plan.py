from dataclasses import dataclass, field
from typing import Any

from educational_planning_v2.models.educational_plan import EducationalPlan
from educational_planning_v2.products.teacher_other_duty import TeacherOtherDuty
from educational_planning_v2.products.teacher_plan_context import TeacherPlanContext


@dataclass(frozen=True)
class TeacherEducationalPlan:
    """Product contract for a teacher educational plan."""

    product_id: str
    context: TeacherPlanContext
    educational_plan: EducationalPlan

    other_duties: tuple[TeacherOtherDuty, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "product_id",
            self._require_text(self.product_id, "product_id"),
        )

        if not isinstance(self.context, TeacherPlanContext):
            raise TypeError(
                "context must be a TeacherPlanContext"
            )

        if not isinstance(self.educational_plan, EducationalPlan):
            raise TypeError(
                "educational_plan must be an EducationalPlan"
            )

        if not isinstance(self.other_duties, tuple):
            raise TypeError(
                "other_duties must be a tuple"
            )

        if not all(
            isinstance(duty, TeacherOtherDuty)
            for duty in self.other_duties
        ):
            raise TypeError(
                "all other_duties must be TeacherOtherDuty instances"
            )

        if not isinstance(self.metadata, dict):
            raise TypeError(
                "metadata must be a dict"
            )

    @staticmethod
    def _require_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized