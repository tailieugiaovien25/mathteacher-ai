from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
)


@dataclass(frozen=True)
class LegacyAssignmentMigrationPreview:
    assignment_id: str
    is_legacy: bool
    can_auto_migrate: bool
    class_refs: tuple[str, ...]
    subject_refs: tuple[str, ...]
    component_refs: tuple[str, ...]
    reason: str


class TeachingAssignmentLegacyMigrationService:
    @staticmethod
    def _split(
        value: str | None,
    ) -> tuple[str, ...]:
        if value is None:
            return ()

        normalized = value.replace(
            ";",
            ",",
        )

        return tuple(
            item.strip()
            for item in normalized.split(",")
            if item.strip()
        )

    def preview(
        self,
        assignment: TeachingAssignment,
    ) -> LegacyAssignmentMigrationPreview:
        class_refs = self._split(
            assignment.class_id
        )

        subject_refs = self._split(
            assignment.subject_ref
        )

        component_refs = self._split(
            assignment.component_ref
        )

        is_legacy = any(
            len(values) > 1
            for values in (
                class_refs,
                subject_refs,
                component_refs,
            )
        )

        if not is_legacy:
            return LegacyAssignmentMigrationPreview(
                assignment_id=assignment.assignment_id,
                is_legacy=False,
                can_auto_migrate=False,
                class_refs=class_refs,
                subject_refs=subject_refs,
                component_refs=component_refs,
                reason="Assignment is already atomic.",
            )

        if (
            assignment.role
            is not TeachingAssignmentRole.TEACHING
        ):
            return LegacyAssignmentMigrationPreview(
                assignment_id=assignment.assignment_id,
                is_legacy=True,
                can_auto_migrate=False,
                class_refs=class_refs,
                subject_refs=subject_refs,
                component_refs=component_refs,
                reason=(
                    "Legacy non-teaching assignment "
                    "requires manual review."
                ),
            )

        if (
            len(class_refs) == 1
            and len(subject_refs) == 1
            and len(component_refs) <= 1
        ):
            return LegacyAssignmentMigrationPreview(
                assignment_id=assignment.assignment_id,
                is_legacy=True,
                can_auto_migrate=True,
                class_refs=class_refs,
                subject_refs=subject_refs,
                component_refs=component_refs,
                reason=(
                    "Legacy delimiters can be normalized "
                    "without changing assignment meaning."
                ),
            )

        return LegacyAssignmentMigrationPreview(
            assignment_id=assignment.assignment_id,
            is_legacy=True,
            can_auto_migrate=False,
            class_refs=class_refs,
            subject_refs=subject_refs,
            component_refs=component_refs,
            reason=(
                "Multiple teaching dimensions are present; "
                "class-subject-component relationships "
                "cannot be inferred safely."
            ),
        )
