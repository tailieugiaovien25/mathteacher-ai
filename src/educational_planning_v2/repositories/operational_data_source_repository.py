from __future__ import annotations

from abc import ABC, abstractmethod

from educational_planning_v2.models.operational_data_source import (
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)


class OperationalDataSourceRepository(ABC):
    """
    Storage-neutral repository contract for operational-data
    source catalog metadata.

    The repository stores source metadata only. It does not own
    PPCT rows, timetable rows, workbook bytes, document bytes,
    or any other educational payload.
    """

    @abstractmethod
    def save(
        self,
        *,
        source: OperationalDataSource,
    ) -> OperationalDataSource:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        *,
        source_id: str,
    ) -> OperationalDataSource | None:
        raise NotImplementedError

    @abstractmethod
    def list_sources(
        self,
        *,
        owner_id: str | None = None,
        academic_year: str | None = None,
        data_type: OperationalDataType | None = None,
        status: OperationalDataStatus | None = None,
    ) -> tuple[OperationalDataSource, ...]:
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        *,
        source_id: str,
    ) -> None:
        raise NotImplementedError
