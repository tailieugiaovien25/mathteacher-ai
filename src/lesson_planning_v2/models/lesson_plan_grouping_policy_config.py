from __future__ import annotations

from dataclasses import dataclass

from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroupingMode


@dataclass(frozen=True, slots=True)
class LessonPlanGroupingPolicyConfig:
    subject_ref: str
    component_ref: str
    mode: LessonPlanGroupingMode
    active: bool = True
    source: str = "ADMIN_CANONICAL_CONFIG"
    version: int = 1

    def __post_init__(self) -> None:
        subject = str(self.subject_ref or "").strip()
        component = str(self.component_ref or "").strip()
        if not subject:
            raise ValueError("SUBJECT_REF_REQUIRED")
        if int(self.version) < 1:
            raise ValueError("POLICY_VERSION_MUST_BE_POSITIVE")
        object.__setattr__(self, "subject_ref", subject)
        object.__setattr__(self, "component_ref", component)
