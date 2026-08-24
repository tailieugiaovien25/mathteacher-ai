from __future__ import annotations

from abc import ABC, abstractmethod

from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)


class TeachingAssignmentRepository(ABC):
    @abstractmethod
    def save(
        self,
        *,
        assignment: TeachingAssignment,
    ) -> TeachingAssignment:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        *,
        assignment_id: str,
    ) -> TeachingAssignment | None:
        raise NotImplementedError

    @abstractmethod
    def list_assignments(
        self,
        *,
        owner_id: str,
        academic_year: str,
        role: TeachingAssignmentRole | None = None,
        status: TeachingAssignmentStatus | None = None,
    ) -> tuple[TeachingAssignment, ...]:
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        *,
        assignment_id: str,
    ) -> None:
        raise NotImplementedError
