from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.models import (
    CurriculumScope,
    EducationalPlan,
    EducationalPlanItem,
)
from educational_planning_v2.validators import EducationalPlanValidator


@dataclass(frozen=True)
class PlanItemDraft:
    """Input contract used to construct one educational plan item."""

    title: str
    periods: int

    curriculum_node_ids: tuple[str, ...] = ()
    canonical_requirement_ids: tuple[str, ...] = ()

    planned_time: str | None = None
    teaching_equipment: tuple[str, ...] = ()
    teaching_location: str | None = None


class EducationalPlanBuilder:
    """Build validated educational plans from canonical references."""

    def __init__(
        self,
        validator: EducationalPlanValidator | None = None,
    ) -> None:
        self._validator = validator or EducationalPlanValidator()

    def build(
        self,
        *,
        educational_plan_id: str,
        academic_year: str,
        subject: str,
        grade: int,
        curriculum_ref: str,
        item_drafts: tuple[PlanItemDraft, ...],
        status: str = "DRAFT",
    ) -> EducationalPlan:
        items = tuple(
            self._build_item(
                draft=draft,
                grade=grade,
                curriculum_ref=curriculum_ref,
                sequence=index,
                plan_id=educational_plan_id,
            )
            for index, draft in enumerate(item_drafts, start=1)
        )

        plan = EducationalPlan(
            educational_plan_id=educational_plan_id,
            academic_year=academic_year,
            subject=subject,
            grade=grade,
            items=items,
            status=status,
        )

        result = self._validator.validate(plan)
        if not result.is_valid:
            details = "; ".join(
                f"{violation.code}: {violation.message}"
                for violation in result.violations
            )
            raise ValueError(f"Educational plan is invalid: {details}")

        return plan

    @staticmethod
    def _build_item(
        *,
        draft: PlanItemDraft,
        grade: int,
        curriculum_ref: str,
        sequence: int,
        plan_id: str,
    ) -> EducationalPlanItem:
        scope = CurriculumScope(
            curriculum_ref=curriculum_ref,
            grade=grade,
            curriculum_node_ids=draft.curriculum_node_ids,
            canonical_requirement_ids=draft.canonical_requirement_ids,
        )

        return EducationalPlanItem(
            plan_item_id=f"{plan_id}-ITEM-{sequence:03d}",
            title=draft.title,
            curriculum_scope=scope,
            periods=draft.periods,
            sequence=sequence,
            planned_time=draft.planned_time,
            teaching_equipment=draft.teaching_equipment,
            teaching_location=draft.teaching_location,
        )


def get_educational_plan_builder() -> EducationalPlanBuilder:
    return EducationalPlanBuilder()
