from typing import Any

from educational_planning_v2.models.educational_plan import EducationalPlan
from educational_planning_v2.products import (
    TeacherEducationalPlan,
    TeacherOtherDuty,
    TeacherPlanContext,
)


class TeacherEducationalPlanBuilder:
    """Build a teacher educational-plan product from existing domain data."""

    def build(
        self,
        *,
        product_id: str,
        context: TeacherPlanContext,
        educational_plan: EducationalPlan,
        other_duties: tuple[TeacherOtherDuty, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> TeacherEducationalPlan:
        if not isinstance(context, TeacherPlanContext):
            raise TypeError(
                "context must be a TeacherPlanContext"
            )

        if not isinstance(educational_plan, EducationalPlan):
            raise TypeError(
                "educational_plan must be an EducationalPlan"
            )

        if context.academic_year != educational_plan.academic_year:
            raise ValueError(
                "context academic_year must match "
                "educational_plan academic_year"
            )

        if not isinstance(other_duties, tuple):
            raise TypeError(
                "other_duties must be a tuple"
            )

        if metadata is None:
            product_metadata = {}
        else:
            if not isinstance(metadata, dict):
                raise TypeError(
                    "metadata must be a dict"
                )

            product_metadata = dict(metadata)

        return TeacherEducationalPlan(
            product_id=product_id,
            context=context,
            educational_plan=educational_plan,
            other_duties=other_duties,
            metadata=product_metadata,
        )
