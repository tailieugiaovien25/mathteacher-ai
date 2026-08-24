from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.models.teacher_subject_registration import (
    TeacherSubjectRegistration,
    TeacherSubjectRegistrationStatus,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)


@dataclass(frozen=True)
class TeacherSubjectAssignmentConsistencyIssue:
    assignment: TeachingAssignment
    reason: str


@dataclass(frozen=True)
class TeacherSubjectAssignmentConsistencyResult:
    assignments: tuple[TeachingAssignment, ...]
    registrations: tuple[TeacherSubjectRegistration, ...]
    issues: tuple[TeacherSubjectAssignmentConsistencyIssue, ...]

    @property
    def is_consistent(self) -> bool:
        return not self.issues


class TeacherSubjectAssignmentConsistencyService:
    """
    Audit consistency between active teaching assignments and
    active teacher subject registrations.

    This service owns no persistence, Supabase, UI, subject catalog,
    class catalog, or fixed educational values.
    """

    def audit(
        self,
        *,
        assignments: tuple[TeachingAssignment, ...],
        registrations: tuple[TeacherSubjectRegistration, ...],
    ) -> TeacherSubjectAssignmentConsistencyResult:
        if not isinstance(assignments, tuple):
            raise TypeError(
                "assignments must be a tuple"
            )

        if not isinstance(registrations, tuple):
            raise TypeError(
                "registrations must be a tuple"
            )

        for assignment in assignments:
            if not isinstance(
                assignment,
                TeachingAssignment,
            ):
                raise TypeError(
                    "assignments contain invalid value"
                )

        for registration in registrations:
            if not isinstance(
                registration,
                TeacherSubjectRegistration,
            ):
                raise TypeError(
                    "registrations contain invalid value"
                )

        active_registrations = tuple(
            registration
            for registration in registrations
            if (
                registration.status
                is TeacherSubjectRegistrationStatus.ACTIVE
            )
        )

        issues = []

        for assignment in assignments:
            if (
                assignment.role
                is not TeachingAssignmentRole.TEACHING
                or assignment.status
                is not TeachingAssignmentStatus.ACTIVE
            ):
                continue

            if assignment.subject_ref is None:
                issues.append(
                    TeacherSubjectAssignmentConsistencyIssue(
                        assignment=assignment,
                        reason=(
                            "active teaching assignment "
                            "has no subject_ref"
                        ),
                    )
                )
                continue

            matches = tuple(
                registration
                for registration in active_registrations
                if (
                    registration.owner_id
                    == assignment.owner_id
                    and registration.academic_year
                    == assignment.academic_year
                    and registration.subject_id
                    == assignment.subject_ref
                    and registration.component_id
                    == assignment.component_ref
                )
            )

            if not matches:
                issues.append(
                    TeacherSubjectAssignmentConsistencyIssue(
                        assignment=assignment,
                        reason=(
                            "active teaching assignment "
                            "has no matching active "
                            "subject registration"
                        ),
                    )
                )

        return TeacherSubjectAssignmentConsistencyResult(
            assignments=assignments,
            registrations=registrations,
            issues=tuple(issues),
        )
