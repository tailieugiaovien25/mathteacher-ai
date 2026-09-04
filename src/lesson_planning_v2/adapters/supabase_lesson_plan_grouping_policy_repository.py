from __future__ import annotations

from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroupingMode
from lesson_planning_v2.models.lesson_plan_grouping_policy_config import (
    LessonPlanGroupingPolicyConfig,
)


class SupabaseLessonPlanGroupingPolicyRepository:
    TABLE = "lesson_plan_grouping_policy_config"

    def __init__(self, client) -> None:
        self.client = client

    @staticmethod
    def _from_row(row) -> LessonPlanGroupingPolicyConfig:
        raw_mode = str(row.get("grouping_mode", "BY_PERIOD") or "BY_PERIOD")
        # Runtime bridge for rows created before grade became a mandatory partition.
        if raw_mode == "BY_GRADE":
            raw_mode = "BY_WEEK"
        return LessonPlanGroupingPolicyConfig(
            subject_ref=str(row.get("subject_ref", "") or ""),
            component_ref=str(row.get("component_ref", "") or ""),
            mode=LessonPlanGroupingMode(raw_mode),
            active=str(row.get("status", "ACTIVE")).upper() == "ACTIVE",
            source="ADMIN_CANONICAL_CONFIG",
            version=int(row.get("rule_version", 1) or 1),
        )

    def list_configs(self, *, include_inactive: bool = False):
        query = self.client.table(self.TABLE).select(
            "subject_ref,component_ref,grouping_mode,status,rule_version"
        )
        if not include_inactive:
            query = query.eq("status", "ACTIVE")
        response = query.order("subject_ref").order("component_ref").execute()
        return tuple(self._from_row(row) for row in (response.data or ()))

    def upsert_config(self, config: LessonPlanGroupingPolicyConfig):
        payload = {
            "subject_ref": config.subject_ref,
            "component_ref": config.component_ref,
            "grouping_mode": config.mode.value,
            "status": "ACTIVE" if config.active else "INACTIVE",
            "rule_version": int(config.version),
        }
        response = (
            self.client.table(self.TABLE)
            .upsert(payload, on_conflict="subject_ref,component_ref")
            .execute()
        )
        rows = response.data or ()
        return self._from_row(rows[0]) if rows else config
