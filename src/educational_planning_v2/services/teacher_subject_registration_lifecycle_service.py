from __future__ import annotations

from dataclasses import replace

from educational_planning_v2.models.teacher_subject_registration import (
    TeacherSubjectRegistration,
    TeacherSubjectRegistrationStatus,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)
from educational_planning_v2.repositories.teacher_subject_registration_repository import (
    TeacherSubjectRegistrationRepository,
)
from educational_planning_v2.repositories.teaching_assignment_repository import (
    TeachingAssignmentRepository,
)


class TeacherSubjectRegistrationLifecycleService:
    def __init__(
        self,
        *,
        registration_repository: (
            TeacherSubjectRegistrationRepository
        ),
        assignment_repository: (
            TeachingAssignmentRepository
        ),
    ) -> None:
        if not isinstance(
            registration_repository,
            TeacherSubjectRegistrationRepository,
        ):
            raise TypeError(
                "registration_repository must implement "
                "TeacherSubjectRegistrationRepository"
            )

        if not isinstance(
            assignment_repository,
            TeachingAssignmentRepository,
        ):
            raise TypeError(
                "assignment_repository must implement "
                "TeachingAssignmentRepository"
            )

        self._registration_repository = (
            registration_repository
        )
        self._assignment_repository = (
            assignment_repository
        )

    def deactivate(
        self,
        *,
        registration_id: str,
    ) -> TeacherSubjectRegistration:
        if not isinstance(
            registration_id,
            str,
        ):
            raise TypeError(
                "registration_id must be str"
            )

        normalized_id = (
            registration_id.strip()
        )

        if not normalized_id:
            raise ValueError(
                "registration_id must not be empty"
            )

        registration = (
            self._registration_repository.get(
                registration_id=normalized_id
            )
        )

        if registration is None:
            raise LookupError(
                "teacher subject registration "
                "not found"
            )

        if (
            registration.status
            is TeacherSubjectRegistrationStatus.INACTIVE
        ):
            return registration

        assignments = (
            self._assignment_repository.list_assignments(
                owner_id=registration.owner_id,
                academic_year=registration.academic_year,
                role=TeachingAssignmentRole.TEACHING,
                status=TeachingAssignmentStatus.ACTIVE,
            )
        )

        blockers = tuple(
            assignment
            for assignment in assignments
            if (
                assignment.subject_ref
                == registration.subject_id
                and (
                    assignment.component_ref
                    or None
                )
                == (
                    registration.component_id
                    or None
                )
            )
        )

        if blockers:
            raise ValueError(
                "registration is used by active "
                "teaching assignments"
            )

        updated = replace(
            registration,
            status=(
                TeacherSubjectRegistrationStatus.INACTIVE
            ),
        )

        return (
            self._registration_repository.save(
                registration=updated
            )
        )
