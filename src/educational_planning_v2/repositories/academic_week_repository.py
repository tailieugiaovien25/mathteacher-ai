from __future__ import annotations

from abc import ABC, abstractmethod

from educational_planning_v2.models.academic_week_configuration import (
    AcademicWeekConfiguration,
)


class AcademicWeekRepository(ABC):

    @abstractmethod
    def save(
        self,
        *,
        week: AcademicWeekConfiguration,
    ) -> AcademicWeekConfiguration:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        *,
        academic_week_id: str,
    ) -> AcademicWeekConfiguration | None:
        raise NotImplementedError

    @abstractmethod
    def get_week(
        self,
        *,
        academic_year_id: str,
        week_number: int,
    ) -> AcademicWeekConfiguration | None:
        raise NotImplementedError

    @abstractmethod
    def list_weeks(
        self,
        *,
        academic_year_id: str,
    ) -> tuple[AcademicWeekConfiguration, ...]:
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        *,
        academic_week_id: str,
    ) -> None:
        raise NotImplementedError
