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
from educational_planning_v2.services.teacher_subject_assignment_consistency_service import (
    TeacherSubjectAssignmentConsistencyService,
)


def make_registration(
    *,
    registration_id="reg-1",
    owner_id="teacher-1",
    academic_year="2026-2027",
    subject_id="SUBJECT-A",
    component_id="COMPONENT-A",
    status=TeacherSubjectRegistrationStatus.ACTIVE,
):
    return TeacherSubjectRegistration(
        registration_id=registration_id,
        owner_id=owner_id,
        academic_year=academic_year,
        subject_id=subject_id,
        component_id=component_id,
        status=status,
    )


def make_assignment(
    *,
    assignment_id="assignment-1",
    owner_id="teacher-1",
    academic_year="2026-2027",
    class_id="6A1",
    subject_ref="SUBJECT-A",
    component_ref="COMPONENT-A",
    role=TeachingAssignmentRole.TEACHING,
    status=TeachingAssignmentStatus.ACTIVE,
):
    return TeachingAssignment(
        assignment_id=assignment_id,
        owner_id=owner_id,
        academic_year=academic_year,
        class_id=class_id,
        role=role,
        subject_ref=subject_ref,
        component_ref=component_ref,
        effective_from=date(2026, 9, 1),
        effective_to=date(2027, 5, 31),
        status=status,
    )


def test_matching_active_registration_is_consistent():
    result = (
        TeacherSubjectAssignmentConsistencyService()
        .audit(
            assignments=(
                make_assignment(),
            ),
            registrations=(
                make_registration(),
            ),
        )
    )

    assert result.is_consistent
    assert result.issues == ()


def test_missing_registration_is_reported():
    result = (
        TeacherSubjectAssignmentConsistencyService()
        .audit(
            assignments=(
                make_assignment(),
            ),
            registrations=(),
        )
    )

    assert not result.is_consistent
    assert len(result.issues) == 1

    issue = result.issues[0]

    assert (
        issue.assignment.assignment_id
        == "assignment-1"
    )

    assert (
        "no matching active subject registration"
        in issue.reason
    )


def test_wrong_component_is_reported():
    result = (
        TeacherSubjectAssignmentConsistencyService()
        .audit(
            assignments=(
                make_assignment(
                    component_ref="COMPONENT-B",
                ),
            ),
            registrations=(
                make_registration(
                    component_id="COMPONENT-A",
                ),
            ),
        )
    )

    assert not result.is_consistent
    assert len(result.issues) == 1


def test_inactive_registration_does_not_satisfy_assignment():
    result = (
        TeacherSubjectAssignmentConsistencyService()
        .audit(
            assignments=(
                make_assignment(),
            ),
            registrations=(
                make_registration(
                    status=(
                        TeacherSubjectRegistrationStatus.INACTIVE
                    ),
                ),
            ),
        )
    )

    assert not result.is_consistent
    assert len(result.issues) == 1


def test_one_registration_can_support_multiple_classes():
    result = (
        TeacherSubjectAssignmentConsistencyService()
        .audit(
            assignments=(
                make_assignment(
                    assignment_id="assignment-1",
                    class_id="6A1",
                ),
                make_assignment(
                    assignment_id="assignment-2",
                    class_id="6A2",
                ),
            ),
            registrations=(
                make_registration(),
            ),
        )
    )

    assert result.is_consistent
    assert result.issues == ()


def test_inactive_assignment_is_ignored():
    result = (
        TeacherSubjectAssignmentConsistencyService()
        .audit(
            assignments=(
                make_assignment(
                    status=(
                        TeachingAssignmentStatus.INACTIVE
                    ),
                ),
            ),
            registrations=(),
        )
    )

    assert result.is_consistent


def test_non_teaching_assignment_is_ignored():
    result = (
        TeacherSubjectAssignmentConsistencyService()
        .audit(
            assignments=(
                TeachingAssignment(
                    assignment_id="homeroom-1",
                    owner_id="teacher-1",
                    academic_year="2026-2027",
                    class_id="6A1",
                    role=(
                        TeachingAssignmentRole.HOMEROOM
                    ),
                    subject_ref=None,
                    component_ref=None,
                    effective_from=date(2026, 9, 1),
                    effective_to=date(2027, 5, 31),
                    status=(
                        TeachingAssignmentStatus.ACTIVE
                    ),
                ),
            ),
            registrations=(),
        )
    )

    assert result.is_consistent


def test_non_tuple_inputs_are_rejected():
    service = (
        TeacherSubjectAssignmentConsistencyService()
    )

    with pytest.raises(
        TypeError,
        match="assignments must be a tuple",
    ):
        service.audit(
            assignments=[],
            registrations=(),
        )

    with pytest.raises(
        TypeError,
        match="registrations must be a tuple",
    ):
        service.audit(
            assignments=(),
            registrations=[],
        )
