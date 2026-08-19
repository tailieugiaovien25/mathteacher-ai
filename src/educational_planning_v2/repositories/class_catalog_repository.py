from __future__ import annotations

from abc import ABC, abstractmethod

from educational_planning_v2.models.class_catalog import (
    ClassCatalog,
    ClassCatalogStatus,
)


class ClassCatalogRepository(
    ABC,
):
    @abstractmethod
    def save(
        self,
        *,
        class_item: ClassCatalog,
    ) -> ClassCatalog:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        *,
        class_id: str,
    ) -> ClassCatalog | None:
        raise NotImplementedError

    @abstractmethod
    def list_classes(
        self,
        *,
        academic_year: str,
        grade_level: str | None = None,
        status: ClassCatalogStatus | None = None,
    ) -> tuple[
        ClassCatalog,
        ...,
    ]:
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        *,
        class_id: str,
    ) -> None:
        raise NotImplementedError
