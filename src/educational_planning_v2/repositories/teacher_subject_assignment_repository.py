from __future__ import annotations

from abc import ABC, abstractmethod

from educational_planning_v2.models.teacher_subject_assignment import (
    TeacherSubjectAssignment,
    TeacherSubjectAssignmentStatus,
)


class TeacherSubjectAssignmentRepository(
    ABC
):
    @abstractmethod
    def save(
        self,
        *,
        assignment: TeacherSubjectAssignment,
    ) -> TeacherSubjectAssignment:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        *,
        assignment_id: str,
    ) -> TeacherSubjectAssignment | None:
        raise NotImplementedError

    @abstractmethod
    def list_assignments(
        self,
        *,
        teacher_id: str | None = None,
        academic_year: str | None = None,
        status: TeacherSubjectAssignmentStatus | None = None,
    ) -> tuple[
        TeacherSubjectAssignment,
        ...,
    ]:
        raise NotImplementedError

    @abstractmethod
    def find_subject_scope(
        self,
        *,
        teacher_id: str,
        academic_year: str,
        subject_id: str,
        status: TeacherSubjectAssignmentStatus | None = None,
    ) -> tuple[
        TeacherSubjectAssignment,
        ...,
    ]:
        raise NotImplementedError
