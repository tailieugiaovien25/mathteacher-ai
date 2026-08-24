from datetime import date

import pytest

from educational_planning_v2.models.teacher_subject_registration import (
    TeacherSubjectRegistration,
    TeacherSubjectRegistrationStatus,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)
from educational_planning_v2.repositories.teacher_subject_registration_repository import (
    TeacherSubjectRegistrationRepository,
)
from educational_planning_v2.repositories.teaching_assignment_repository import (
    TeachingAssignmentRepository,
)
from educational_planning_v2.services.teacher_subject_registration_lifecycle_service import (
    TeacherSubjectRegistrationLifecycleService,
)


class MemoryRegistrationRepository(
    TeacherSubjectRegistrationRepository
):
    def __init__(self, registrations=()):
        self.items = {
            item.registration_id: item
            for item in registrations
        }

    def save(self, *, registration):
        self.items[
            registration.registration_id
        ] = registration
        return registration

    def get(self, *, registration_id):
        return self.items.get(
            registration_id
        )

    def list_registrations(
        self,
        *,
        owner_id,
        academic_year,
        status=None,
    ):
        return tuple(
            item
            for item in self.items.values()
            if (
                item.owner_id == owner_id
                and item.academic_year
                == academic_year
                and (
                    status is None
                    or item.status is status
                )
            )
        )

    def find_subject_scope(
        self,
        *,
        owner_id,
        academic_year,
        subject_id,
        status=None,
    ):
        return tuple(
            item
            for item in self.list_registrations(
                owner_id=owner_id,
                academic_year=academic_year,
                status=status,
            )
            if item.subject_id == subject_id
        )

    def delete(self, *, registration_id):
        self.items.pop(
            registration_id,
            None,
        )


class MemoryAssignmentRepository(
    TeachingAssignmentRepository
):
    def __init__(self, assignments=()):
        self.items = {
            item.assignment_id: item
            for item in assignments
        }

    def save(self, *, assignment):
        self.items[
            assignment.assignment_id
        ] = assignment
        return assignment

    def get(self, *, assignment_id):
        return self.items.get(
            assignment_id
        )

    def list_assignments(
        self,
        *,
        owner_id,
        academic_year,
        role=None,
        status=None,
    ):
        return tuple(
            item
            for item in self.items.values()
            if (
                item.owner_id == owner_id
                and item.academic_year
                == academic_year
                and (
                    role is None
                    or item.role is role
                )
                and (
                    status is None
                    or item.status is status
                )
            )
        )

    def delete(self, *, assignment_id):
        self.items.pop(
            assignment_id,
            None,
        )


def registration(
    *,
    status=(
        TeacherSubjectRegistrationStatus.ACTIVE
    ),
):
    return TeacherSubjectRegistration(
        registration_id="reg-1",
        owner_id="teacher-1",
        academic_year="2026-2027",
        subject_id="SUBJECT-A",
        component_id="COMPONENT-A",
        status=status,
    )


def assignment(
    *,
    status=TeachingAssignmentStatus.ACTIVE,
    subject_ref="SUBJECT-A",
    component_ref="COMPONENT-A",
):
    return TeachingAssignment(
        assignment_id="assignment-1",
        owner_id="teacher-1",
        academic_year="2026-2027",
        class_id="6A1",
        role=TeachingAssignmentRole.TEACHING,
        subject_ref=subject_ref,
        component_ref=component_ref,
        effective_from=date(2026, 9, 1),
        effective_to=date(2027, 5, 31),
        status=status,
    )


def test_deactivate_registration_without_dependencies():
    reg_repo = MemoryRegistrationRepository(
        (
            registration(),
        )
    )

    service = (
        TeacherSubjectRegistrationLifecycleService(
            registration_repository=reg_repo,
            assignment_repository=(
                MemoryAssignmentRepository()
            ),
        )
    )

    result = service.deactivate(
        registration_id="reg-1"
    )

    assert (
        result.status
        is TeacherSubjectRegistrationStatus.INACTIVE
    )


def test_active_assignment_blocks_deactivation():
    service = (
        TeacherSubjectRegistrationLifecycleService(
            registration_repository=(
                MemoryRegistrationRepository(
                    (
                        registration(),
                    )
                )
            ),
            assignment_repository=(
                MemoryAssignmentRepository(
                    (
                        assignment(),
                    )
                )
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match=(
            "used by active teaching assignments"
        ),
    ):
        service.deactivate(
            registration_id="reg-1"
        )


def test_inactive_assignment_does_not_block():
    service = (
        TeacherSubjectRegistrationLifecycleService(
            registration_repository=(
                MemoryRegistrationRepository(
                    (
                        registration(),
                    )
                )
            ),
            assignment_repository=(
                MemoryAssignmentRepository(
                    (
                        assignment(
                            status=(
                                TeachingAssignmentStatus.INACTIVE
                            )
                        ),
                    )
                )
            ),
        )
    )

    result = service.deactivate(
        registration_id="reg-1"
    )

    assert (
        result.status
        is TeacherSubjectRegistrationStatus.INACTIVE
    )


def test_other_subject_assignment_does_not_block():
    service = (
        TeacherSubjectRegistrationLifecycleService(
            registration_repository=(
                MemoryRegistrationRepository(
                    (
                        registration(),
                    )
                )
            ),
            assignment_repository=(
                MemoryAssignmentRepository(
                    (
                        assignment(
                            subject_ref="SUBJECT-B"
                        ),
                    )
                )
            ),
        )
    )

    result = service.deactivate(
        registration_id="reg-1"
    )

    assert (
        result.status
        is TeacherSubjectRegistrationStatus.INACTIVE
    )


def test_missing_registration_is_reported():
    service = (
        TeacherSubjectRegistrationLifecycleService(
            registration_repository=(
                MemoryRegistrationRepository()
            ),
            assignment_repository=(
                MemoryAssignmentRepository()
            ),
        )
    )

    with pytest.raises(
        LookupError,
        match="registration.*not found",
    ):
        service.deactivate(
            registration_id="missing"
        )


def test_inactive_registration_is_idempotent():
    existing = registration(
        status=(
            TeacherSubjectRegistrationStatus.INACTIVE
        )
    )

    service = (
        TeacherSubjectRegistrationLifecycleService(
            registration_repository=(
                MemoryRegistrationRepository(
                    (
                        existing,
                    )
                )
            ),
            assignment_repository=(
                MemoryAssignmentRepository()
            ),
        )
    )

    result = service.deactivate(
        registration_id="reg-1"
    )

    assert result is existing
