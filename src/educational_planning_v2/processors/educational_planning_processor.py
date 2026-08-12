from __future__ import annotations
from typing import Any
from core_v2.processing import Processor
from educational_planning_v2 import EducationalPlanningFacade
from educational_planning_v2.builders import PlanItemDraft

class EducationalPlanningProcessor(Processor):
    def __init__(self, facade: EducationalPlanningFacade | None = None) -> None:
        self._facade = facade or EducationalPlanningFacade()

    @property
    def processor_id(self) -> str:
        return "PROC-EDUCATIONAL-PLANNING-V2"

    @property
    def data_type_id(self) -> str:
        return "EDUCATIONAL_PLAN"

    @property
    def capability(self) -> str:
        return "BUILD_EDUCATIONAL_PLAN"

    def process(self, data: Any, *, context: dict[str, Any] | None = None) -> Any:
        if not isinstance(data, dict):
            raise TypeError("educational planning input must be a dict")
        raw_items = data.get("item_drafts", ())
        if not isinstance(raw_items, (list, tuple)):
            raise TypeError("item_drafts must be a list or tuple")
        drafts = tuple(self._to_draft(item) for item in raw_items)
        return self._facade.build_plan(
            educational_plan_id=data["educational_plan_id"],
            academic_year=data["academic_year"],
            subject=data["subject"],
            grade=data["grade"],
            curriculum_ref=data["curriculum_ref"],
            item_drafts=drafts,
            status=data.get("status", "DRAFT"),
        )

    @staticmethod
    def _to_draft(data: Any) -> PlanItemDraft:
        if isinstance(data, PlanItemDraft):
            return data
        if not isinstance(data, dict):
            raise TypeError("each item draft must be a dict or PlanItemDraft")
        return PlanItemDraft(
            title=data["title"],
            periods=data["periods"],
            curriculum_node_ids=tuple(data.get("curriculum_node_ids", ())),
            canonical_requirement_ids=tuple(data.get("canonical_requirement_ids", ())),
            planned_time=data.get("planned_time"),
            teaching_equipment=tuple(data.get("teaching_equipment", ())),
            teaching_location=data.get("teaching_location"),
        )
