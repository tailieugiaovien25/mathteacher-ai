from __future__ import annotations

from educational_planning_v2.adapters.supabase_teacher_subject_registration_repository import (
    SupabaseTeacherSubjectRegistrationRepository,
)
from educational_planning_v2.adapters.supabase_teaching_assignment_repository import (
    SupabaseTeachingAssignmentRepository,
)
from educational_planning_v2.models.teacher_subject_registration import (
    TeacherSubjectRegistrationStatus,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)
from educational_planning_v2.services.teacher_subject_assignment_consistency_service import (
    TeacherSubjectAssignmentConsistencyResult,
    TeacherSubjectAssignmentConsistencyService,
)


class TeacherSubjectAssignmentConsistencyRuntime:
    """
    Authenticated runtime boundary for auditing consistency between
    teacher subject registrations and teaching assignments.

    The runtime owns concrete persistence wiring only.
    Business consistency rules remain in the domain service.
    """

    def __init__(
        self,
        *,
        client,
        user_id: str,
    ) -> None:
        if client is None:
            raise ValueError(
                "client must not be None"
            )

        if not isinstance(
            user_id,
            str,
        ):
            raise TypeError(
                "user_id must be str"
            )

        normalized_user_id = (
            user_id.strip()
        )

        if not normalized_user_id:
            raise ValueError(
                "user_id must not be empty"
            )

        self._client = client
        self._user_id = normalized_user_id

        self._registration_repository = (
            SupabaseTeacherSubjectRegistrationRepository(
                client,
                self._user_id,
            )
        )

        self._assignment_repository = (
            SupabaseTeachingAssignmentRepository(
                client=client,
                user_id=self._user_id,
            )
        )

        self._service = (
            TeacherSubjectAssignmentConsistencyService()
        )

    def audit(
        self,
        *,
        academic_year: str,
    ) -> TeacherSubjectAssignmentConsistencyResult:
        if not isinstance(
            academic_year,
            str,
        ):
            raise TypeError(
                "academic_year must be str"
            )

        normalized_year = (
            academic_year.strip()
        )

        if not normalized_year:
            raise ValueError(
                "academic_year must not be empty"
            )

        registrations = (
            self._registration_repository.list_registrations(
                owner_id=self._user_id,
                academic_year=normalized_year,
                status=(
                    TeacherSubjectRegistrationStatus.ACTIVE
                ),
            )
        )

        assignments = (
            self._assignment_repository.list_assignments(
                owner_id=self._user_id,
                academic_year=normalized_year,
                role=(
                    TeachingAssignmentRole.TEACHING
                ),
                status=(
                    TeachingAssignmentStatus.ACTIVE
                ),
            )
        )

        return self._service.audit(
            assignments=assignments,
            registrations=registrations,
        )
