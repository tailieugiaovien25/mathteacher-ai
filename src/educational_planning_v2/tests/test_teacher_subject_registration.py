import pytest

from educational_planning_v2.models.teacher_subject_registration import (
    TeacherSubjectRegistration,
    TeacherSubjectRegistrationStatus,
)


def test_subject_level_registration_is_valid():
    registration = TeacherSubjectRegistration(
        registration_id="registration-001",
        owner_id="teacher-001",
        academic_year="2026-2027",
        subject_id="subject-math",
    )

    assert registration.is_subject_level
    assert not registration.is_component_level

    assert (
        registration.status
        is TeacherSubjectRegistrationStatus.ACTIVE
    )


def test_component_level_registration_is_valid():
    registration = TeacherSubjectRegistration(
        registration_id="registration-002",
        owner_id="teacher-001",
        academic_year="2026-2027",
        subject_id="subject-math",
        component_id="component-math-algebra",
    )

    assert registration.is_component_level
    assert not registration.is_subject_level


@pytest.mark.parametrize(
    "field_name",
    (
        "registration_id",
        "owner_id",
        "academic_year",
        "subject_id",
    ),
)
def test_required_fields_reject_blank_values(
    field_name,
):
    values = {
        "registration_id": "registration-001",
        "owner_id": "teacher-001",
        "academic_year": "2026-2027",
        "subject_id": "subject-math",
    }

    values[field_name] = " "

    with pytest.raises(
        ValueError,
        match=field_name,
    ):
        TeacherSubjectRegistration(
            **values
        )


def test_blank_component_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="component_id",
    ):
        TeacherSubjectRegistration(
            registration_id="registration-001",
            owner_id="teacher-001",
            academic_year="2026-2027",
            subject_id="subject-math",
            component_id=" ",
        )


def test_invalid_status_type_is_rejected():
    with pytest.raises(
        TypeError,
        match="status",
    ):
        TeacherSubjectRegistration(
            registration_id="registration-001",
            owner_id="teacher-001",
            academic_year="2026-2027",
            subject_id="subject-math",
            status="ACTIVE",
        )
