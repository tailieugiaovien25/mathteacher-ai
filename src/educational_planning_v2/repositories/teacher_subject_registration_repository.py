from __future__ import annotations

from abc import ABC, abstractmethod

from educational_planning_v2.models.teacher_subject_registration import (
    TeacherSubjectRegistration,
    TeacherSubjectRegistrationStatus,
)


class TeacherSubjectRegistrationRepository(ABC):
    @abstractmethod
    def save(
        self,
        *,
        registration: TeacherSubjectRegistration,
    ) -> TeacherSubjectRegistration:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        *,
        registration_id: str,
    ) -> TeacherSubjectRegistration | None:
        raise NotImplementedError

    @abstractmethod
    def list_registrations(
        self,
        *,
        owner_id: str,
        academic_year: str,
        status: (
            TeacherSubjectRegistrationStatus
            | None
        ) = None,
    ) -> tuple[
        TeacherSubjectRegistration,
        ...
    ]:
        raise NotImplementedError

    @abstractmethod
    def find_subject_scope(
        self,
        *,
        owner_id: str,
        academic_year: str,
        subject_id: str,
        status: (
            TeacherSubjectRegistrationStatus
            | None
        ) = None,
    ) -> tuple[
        TeacherSubjectRegistration,
        ...
    ]:
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        *,
        registration_id: str,
    ) -> None:
        raise NotImplementedError
