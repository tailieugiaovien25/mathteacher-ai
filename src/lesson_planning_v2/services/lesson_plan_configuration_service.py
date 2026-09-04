from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from lesson_planning_v2.models.lesson_plan_configuration import (
    LessonPlanConfigurationSnapshot,
)
from lesson_planning_v2.services.configuration_hierarchy import (
    merge_with_parent_authority,
)


@dataclass(frozen=True)
class ResolvedLessonPlanConfiguration:
    source: str
    snapshot: LessonPlanConfigurationSnapshot | None
    configuration_payload: Mapping[str, Any]
    global_snapshot: LessonPlanConfigurationSnapshot | None = None
    subject_snapshot: LessonPlanConfigurationSnapshot | None = None
    locked_paths: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()


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
        exact = getattr(self.repository, "get_active_configuration_exact", None)
        if callable(exact):
            global_snapshot = exact(subject_ref="", component_ref=None)
            subject_snapshot = None
            if str(subject_ref or "").strip():
                subject_snapshot = exact(
                    subject_ref=subject_ref, component_ref=component_ref
                )
            if global_snapshot is not None or subject_snapshot is not None:
                effective, conflicts = merge_with_parent_authority(
                    parent=(global_snapshot.configuration_payload if global_snapshot else {}),
                    child=(subject_snapshot.configuration_payload if subject_snapshot else {}),
                )
                locked_paths = tuple(sorted(_leaf_paths(
                    global_snapshot.configuration_payload if global_snapshot else {}
                )))
                authority = global_snapshot or subject_snapshot
                return ResolvedLessonPlanConfiguration(
                    source=self.SOURCE_ADMIN,
                    snapshot=authority,
                    configuration_payload=effective,
                    global_snapshot=global_snapshot,
                    subject_snapshot=subject_snapshot,
                    locked_paths=locked_paths,
                    conflicts=conflicts,
                )

        snapshot = self.repository.get_active_configuration(
            subject_ref=subject_ref, component_ref=component_ref,
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


def _leaf_paths(value: Mapping[str, Any], prefix: tuple[str, ...] = ()):
    for key, item in value.items():
        path = prefix + (str(key),)
        if isinstance(item, Mapping):
            yield from _leaf_paths(item, path)
        else:
            yield ".".join(path)
