from datetime import date

import pytest

from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)


def _assignment(**changes):
    values = {
        "assignment_id": "assign-001",
        "owner_id": "teacher-001",
        "academic_year": "2026-2027",
        "class_id": "6A2",
        "subject_ref": "Toan",
        "component_ref": "So hoc",
        "role": TeachingAssignmentRole.TEACHING,
        "effective_from": date(2026, 9, 1),
        "effective_to": date(2027, 5, 31),
        "status": TeachingAssignmentStatus.ACTIVE,
    }

    values.update(changes)

    return TeachingAssignment(**values)


def test_teaching_assignment_normalizes_values():
    assignment = _assignment(
        assignment_id=" assign-001 ",
        class_id=" 6A2 ",
        subject_ref=" Toan ",
        component_ref=" So hoc ",
    )

    assert assignment.assignment_id == "assign-001"
    assert assignment.class_id == "6A2"
    assert assignment.subject_ref == "Toan"
    assert assignment.component_ref == "So hoc"


def test_teaching_assignment_exposes_teaching_key():
    assignment = _assignment()

    assert assignment.teaching_key == (
        "6A2",
        "Toan",
        "So hoc",
    )


def test_teaching_assignment_requires_subject_for_teaching():
    with pytest.raises(ValueError):
        _assignment(
            subject_ref=None,
        )


def test_homeroom_assignment_allows_no_subject():
    assignment = _assignment(
        role=TeachingAssignmentRole.HOMEROOM,
        subject_ref=None,
        component_ref=None,
    )

    assert assignment.role is TeachingAssignmentRole.HOMEROOM


def test_homeroom_assignment_blocks_component():
    with pytest.raises(ValueError):
        _assignment(
            role=TeachingAssignmentRole.HOMEROOM,
            subject_ref=None,
            component_ref="So hoc",
        )


def test_assignment_blocks_invalid_date_range():
    with pytest.raises(ValueError):
        _assignment(
            effective_from=date(2027, 6, 1),
            effective_to=date(2026, 9, 1),
        )
