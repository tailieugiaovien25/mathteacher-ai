from __future__ import annotations

from abc import ABC, abstractmethod

from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
    Subject,
    SubjectComponent,
)


class SubjectCatalogRepository(ABC):
    @abstractmethod
    def save_subject(
        self,
        *,
        subject: Subject,
    ) -> Subject:
        raise NotImplementedError

    @abstractmethod
    def save_component(
        self,
        *,
        component: SubjectComponent,
    ) -> SubjectComponent:
        raise NotImplementedError

    @abstractmethod
    def get_subject(
        self,
        *,
        subject_id: str,
    ) -> Subject | None:
        raise NotImplementedError

    @abstractmethod
    def get_component(
        self,
        *,
        component_id: str,
    ) -> SubjectComponent | None:
        raise NotImplementedError

    @abstractmethod
    def list_subjects(
        self,
        *,
        status: CatalogStatus | None = None,
    ) -> tuple[Subject, ...]:
        raise NotImplementedError

    @abstractmethod
    def list_components(
        self,
        *,
        subject_id: str,
        status: CatalogStatus | None = None,
    ) -> tuple[SubjectComponent, ...]:
        raise NotImplementedError
