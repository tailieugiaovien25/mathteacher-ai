from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.models.operational_data_source import (
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.repositories.operational_data_source_repository import (
    OperationalDataSourceRepository,
)


@dataclass(frozen=True)
class OperationalLibraryQuery:
    owner_id: str
    academic_year: str
    data_type: OperationalDataType
    status: OperationalDataStatus = OperationalDataStatus.ACTIVE

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "owner_id",
            self._required_text(
                self.owner_id,
                "owner_id",
            ),
        )

        object.__setattr__(
            self,
            "academic_year",
            self._required_text(
                self.academic_year,
                "academic_year",
            ),
        )

        if not isinstance(
            self.data_type,
            OperationalDataType,
        ):
            raise TypeError(
                "data_type must be OperationalDataType"
            )

        if not isinstance(
            self.status,
            OperationalDataStatus,
        ):
            raise TypeError(
                "status must be OperationalDataStatus"
            )

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be str"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized


@dataclass(frozen=True)
class OperationalLibraryItem:
    source_id: str
    source_name: str
    academic_year: str
    data_type: OperationalDataType
    status: OperationalDataStatus
    source_version: str | None

    @classmethod
    def from_source(
        cls,
        source: OperationalDataSource,
    ) -> "OperationalLibraryItem":
        if not isinstance(
            source,
            OperationalDataSource,
        ):
            raise TypeError(
                "source must be OperationalDataSource"
            )

        return cls(
            source_id=source.source_id,
            source_name=(
                source.source_name
                or source.source_id
            ),
            academic_year=source.academic_year,
            data_type=source.data_type,
            status=source.status,
            source_version=source.source_version,
        )


class OperationalLibraryQueryService:
    """
    Read-only catalog query service for operational data.

    The service exposes library metadata only and does not
    retrieve or interpret educational payload.
    """

    def __init__(
        self,
        repository: OperationalDataSourceRepository,
    ) -> None:
        if not isinstance(
            repository,
            OperationalDataSourceRepository,
        ):
            raise TypeError(
                "repository must implement "
                "OperationalDataSourceRepository"
            )

        self._repository = repository

    def query(
        self,
        *,
        query: OperationalLibraryQuery,
    ) -> tuple[OperationalLibraryItem, ...]:
        if not isinstance(
            query,
            OperationalLibraryQuery,
        ):
            raise TypeError(
                "query must be OperationalLibraryQuery"
            )

        sources = self._repository.list_sources(
            owner_id=query.owner_id,
            academic_year=query.academic_year,
            data_type=query.data_type,
            status=query.status,
        )

        if not isinstance(
            sources,
            tuple,
        ):
            raise TypeError(
                "repository must return tuple"
            )

        if not all(
            isinstance(
                source,
                OperationalDataSource,
            )
            for source in sources
        ):
            raise TypeError(
                "repository returned invalid source"
            )

        ordered = tuple(
            sorted(
                sources,
                key=lambda source: (
                    source.source_name or "",
                    source.source_version or "",
                    source.source_id,
                ),
            )
        )

        return tuple(
            OperationalLibraryItem.from_source(
                source
            )
            for source in ordered
        )
