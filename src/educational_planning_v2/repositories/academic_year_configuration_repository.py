from __future__ import annotations

from abc import ABC, abstractmethod

from educational_planning_v2.models.academic_year_configuration import (
    AcademicYearConfiguration,
)


class AcademicYearConfigurationRepository(
    ABC
):
    @abstractmethod
    def save(
        self,
        *,
        configuration: AcademicYearConfiguration,
    ) -> AcademicYearConfiguration:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        *,
        academic_year_id: str,
    ) -> AcademicYearConfiguration | None:
        raise NotImplementedError

    @abstractmethod
    def get_current(
        self,
    ) -> AcademicYearConfiguration | None:
        raise NotImplementedError

    @abstractmethod
    def list_configurations(
        self,
    ) -> tuple[
        AcademicYearConfiguration,
        ...,
    ]:
        raise NotImplementedError

    @abstractmethod
    def set_current(
        self,
        *,
        academic_year_id: str,
    ) -> AcademicYearConfiguration:
        raise NotImplementedError
