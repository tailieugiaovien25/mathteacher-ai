import pytest

from educational_planning_v2.models.teacher_subject_assignment import (
    TeacherSubjectAssignment,
    TeacherSubjectAssignmentStatus,
)


def make_assignment(
    *,
    assignment_id="tsa-1",
    teacher_id="teacher-1",
    academic_year="2026-2027",
    subject_id="SUBJECT-MATH",
    status=TeacherSubjectAssignmentStatus.ACTIVE,
):
    return TeacherSubjectAssignment(
        assignment_id=assignment_id,
        teacher_id=teacher_id,
        academic_year=academic_year,
        subject_id=subject_id,
        status=status,
    )


def test_teacher_subject_assignment_is_valid():
    assignment = make_assignment()

    assert assignment.assignment_id == "tsa-1"
    assert assignment.teacher_id == "teacher-1"
    assert assignment.academic_year == "2026-2027"
    assert assignment.subject_id == "SUBJECT-MATH"
    assert (
        assignment.status
        is TeacherSubjectAssignmentStatus.ACTIVE
    )


def test_assignment_key_is_canonical():
    assignment = make_assignment()

    assert assignment.assignment_key == (
        "teacher-1",
        "2026-2027",
        "SUBJECT-MATH",
    )


@pytest.mark.parametrize(
    "field_name",
    (
        "assignment_id",
        "teacher_id",
        "academic_year",
        "subject_id",
    ),
)
def test_required_fields_reject_blank_values(
    field_name,
):
    values = {
        "assignment_id": "tsa-1",
        "teacher_id": "teacher-1",
        "academic_year": "2026-2027",
        "subject_id": "SUBJECT-MATH",
    }

    values[field_name] = "   "

    with pytest.raises(
        ValueError,
        match=(
            f"{field_name} must not be empty"
        ),
    ):
        TeacherSubjectAssignment(
            **values,
        )


def test_required_fields_are_normalized():
    assignment = make_assignment(
        assignment_id="  tsa-1  ",
        teacher_id="  teacher-1  ",
        academic_year="  2026-2027  ",
        subject_id="  SUBJECT-MATH  ",
    )

    assert assignment.assignment_id == "tsa-1"
    assert assignment.teacher_id == "teacher-1"
    assert assignment.academic_year == "2026-2027"
    assert assignment.subject_id == "SUBJECT-MATH"


def test_invalid_status_type_is_rejected():
    with pytest.raises(
        TypeError,
        match=(
            "status must be "
            "TeacherSubjectAssignmentStatus"
        ),
    ):
        make_assignment(
            status="ACTIVE",
        )
