from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from lesson_planning_v2.models.lesson_plan_configuration import (
    LessonPlanConfigurationSnapshot,
)


@dataclass(frozen=True)
class ResolvedLessonPlanConfiguration:
    source: str
    snapshot: LessonPlanConfigurationSnapshot | None
    configuration_payload: Mapping[str, Any]


class LessonPlanConfigurationService:
    SOURCE_ADMIN = "ADMIN_ACTIVE"
    SOURCE_CURRENT_DEFAULT = "CURRENT_CODE_DEFAULT"

    def __init__(self, repository) -> None:
        self.repository = repository

    def resolve(
        self,
        *,
        subject_ref: str,
        component_ref: str | None = None,
        fallback_payload: Mapping[str, Any] | None = None,
    ) -> ResolvedLessonPlanConfiguration:
        snapshot = self.repository.get_active_configuration(
            subject_ref=subject_ref,
            component_ref=component_ref,
        )
        if snapshot is not None:
            return ResolvedLessonPlanConfiguration(
                source=self.SOURCE_ADMIN,
                snapshot=snapshot,
                configuration_payload=dict(snapshot.configuration_payload),
            )

        return ResolvedLessonPlanConfiguration(
            source=self.SOURCE_CURRENT_DEFAULT,
            snapshot=None,
            configuration_payload=dict(fallback_payload or {}),
        )
