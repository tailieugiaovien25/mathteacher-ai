from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.models.operational_data_io import (
    OperationalInputLocation,
    OperationalInputReference,
)
from educational_planning_v2.models.operational_data_source import (
    OperationalDataSource,
    OperationalDataStatus,
)
from educational_planning_v2.repositories.operational_data_source_repository import (
    OperationalDataSourceRepository,
)


@dataclass(frozen=True)
class OperationalInputSelection:
    """
    Result of resolving an operational input reference.

    LOCAL_UPLOAD has no catalog source yet.

    SYSTEM_LIBRARY resolves to one ACTIVE catalog source.
    """

    reference: OperationalInputReference
    source: OperationalDataSource | None

    def __post_init__(self) -> None:
        if not isinstance(
            self.reference,
            OperationalInputReference,
        ):
            raise TypeError(
                "reference must be OperationalInputReference"
            )

        if (
            self.source is not None
            and not isinstance(
                self.source,
                OperationalDataSource,
            )
        ):
            raise TypeError(
                "source must be OperationalDataSource or None"
            )

        if (
            self.reference.location
            is OperationalInputLocation.SYSTEM_LIBRARY
            and self.source is None
        ):
            raise ValueError(
                "SYSTEM_LIBRARY selection requires source"
            )

        if (
            self.reference.location
            is OperationalInputLocation.LOCAL_UPLOAD
            and self.source is not None
        ):
            raise ValueError(
                "LOCAL_UPLOAD selection must not own catalog source"
            )


class OperationalInputSelectionService:
    """
    Resolve user/application input choice without performing
    physical file I/O or storage operations.
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

    def select(
        self,
        *,
        reference: OperationalInputReference,
    ) -> OperationalInputSelection:
        if not isinstance(
            reference,
            OperationalInputReference,
        ):
            raise TypeError(
                "reference must be OperationalInputReference"
            )

        if (
            reference.location
            is OperationalInputLocation.LOCAL_UPLOAD
        ):
            return OperationalInputSelection(
                reference=reference,
                source=None,
            )

        if (
            reference.location
            is OperationalInputLocation.SYSTEM_LIBRARY
        ):
            return self._select_system_library(
                reference=reference,
            )

        if (
            reference.location
            is OperationalInputLocation.SYSTEM_GENERATED
        ):
            return OperationalInputSelection(
                reference=reference,
                source=None,
            )

        raise ValueError(
            "unsupported operational input location"
        )

    def _select_system_library(
        self,
        *,
        reference: OperationalInputReference,
    ) -> OperationalInputSelection:
        source_id = reference.source_id

        if source_id is None:
            raise ValueError(
                "SYSTEM_LIBRARY input requires source_id"
            )

        source = self._repository.get(
            source_id=source_id,
        )

        if source is None:
            raise LookupError(
                f"operational data source not found: {source_id}"
            )

        if (
            source.status
            is not OperationalDataStatus.ACTIVE
        ):
            raise ValueError(
                "only ACTIVE operational data sources "
                "can be selected from system library"
            )

        if (
            reference.source_academic_year is not None
            and
            source.academic_year
            != reference.source_academic_year
        ):
            raise ValueError(
                "source academic year does not match "
                "input reference"
            )

        return OperationalInputSelection(
            reference=reference,
            source=source,
        )
