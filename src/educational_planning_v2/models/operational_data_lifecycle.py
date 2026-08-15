from __future__ import annotations

from dataclasses import dataclass, replace

from educational_planning_v2.models.operational_data_io import (
    OperationalInputLocation,
    OperationalInputReference,
)
from educational_planning_v2.models.operational_data_source import (
    OperationalDataOrigin,
    OperationalDataSource,
    OperationalDataStatus,
)


@dataclass(frozen=True)
class OperationalDataDerivation:
    """
    Represents a new operational data source derived from an
    immutable historical source stored in the system library.
    """

    derived_source: OperationalDataSource
    input_reference: OperationalInputReference

    def __post_init__(self) -> None:
        if not isinstance(
            self.derived_source,
            OperationalDataSource,
        ):
            raise TypeError(
                "derived_source must be OperationalDataSource"
            )

        if not isinstance(
            self.input_reference,
            OperationalInputReference,
        ):
            raise TypeError(
                "input_reference must be OperationalInputReference"
            )

        if (
            self.input_reference.location
            is not OperationalInputLocation.SYSTEM_LIBRARY
        ):
            raise ValueError(
                "derivation must reference SYSTEM_LIBRARY"
            )


class OperationalDataLifecyclePolicy:
    """
    Owns legal state transitions for operational data sources.

    The policy is generic:
    - it does not know PPCT rows,
    - it does not know Excel,
    - it does not know Supabase,
    - it does not know Google Drive,
    - it does not contain educational values.
    """

    _TRANSITIONS = {
        OperationalDataOrigin.FILE_IMPORTED: {
            OperationalDataStatus.UPLOADED: (
                OperationalDataStatus.MAPPED,
            ),
            OperationalDataStatus.MAPPED: (
                OperationalDataStatus.VALIDATED,
            ),
            OperationalDataStatus.VALIDATED: (
                OperationalDataStatus.ACTIVE,
            ),
            OperationalDataStatus.ACTIVE: (
                OperationalDataStatus.SUPERSEDED,
            ),
            OperationalDataStatus.SUPERSEDED: (),
        },
        OperationalDataOrigin.USER_ENTERED: {
            OperationalDataStatus.UPLOADED: (
                OperationalDataStatus.VALIDATED,
            ),
            OperationalDataStatus.MAPPED: (),
            OperationalDataStatus.VALIDATED: (
                OperationalDataStatus.ACTIVE,
            ),
            OperationalDataStatus.ACTIVE: (
                OperationalDataStatus.SUPERSEDED,
            ),
            OperationalDataStatus.SUPERSEDED: (),
        },
        OperationalDataOrigin.ADMIN_ENTERED: {
            OperationalDataStatus.UPLOADED: (
                OperationalDataStatus.VALIDATED,
            ),
            OperationalDataStatus.MAPPED: (),
            OperationalDataStatus.VALIDATED: (
                OperationalDataStatus.ACTIVE,
            ),
            OperationalDataStatus.ACTIVE: (
                OperationalDataStatus.SUPERSEDED,
            ),
            OperationalDataStatus.SUPERSEDED: (),
        },
        OperationalDataOrigin.SYSTEM_GENERATED: {
            OperationalDataStatus.UPLOADED: (),
            OperationalDataStatus.MAPPED: (),
            OperationalDataStatus.VALIDATED: (
                OperationalDataStatus.ACTIVE,
            ),
            OperationalDataStatus.ACTIVE: (
                OperationalDataStatus.SUPERSEDED,
            ),
            OperationalDataStatus.SUPERSEDED: (),
        },
    }

    def can_transition(
        self,
        *,
        source: OperationalDataSource,
        target_status: OperationalDataStatus,
    ) -> bool:
        self._validate_source(source)
        self._validate_status(target_status)

        allowed = self._TRANSITIONS[
            source.origin
        ].get(
            source.status,
            (),
        )

        return target_status in allowed

    def transition(
        self,
        *,
        source: OperationalDataSource,
        target_status: OperationalDataStatus,
    ) -> OperationalDataSource:
        self._validate_source(source)
        self._validate_status(target_status)

        if not self.can_transition(
            source=source,
            target_status=target_status,
        ):
            raise ValueError(
                "invalid operational data transition: "
                f"{source.origin.value}/"
                f"{source.status.value} -> "
                f"{target_status.value}"
            )

        return replace(
            source,
            status=target_status,
        )

    def derive_for_academic_year(
        self,
        *,
        historical_source: OperationalDataSource,
        new_source_id: str,
        new_academic_year: str,
        owner_id: str | None = None,
        source_name: str | None = None,
        source_version: str | None = None,
    ) -> OperationalDataDerivation:
        """
        Create a NEW source for another academic year.

        Historical source is never mutated.

        The derived source starts at UPLOADED so that reused
        historical data must be checked again before becoming ACTIVE.
        """

        self._validate_source(
            historical_source
        )

        normalized_source_id = self._required_text(
            new_source_id,
            "new_source_id",
        )

        normalized_year = self._required_text(
            new_academic_year,
            "new_academic_year",
        )

        if normalized_source_id == historical_source.source_id:
            raise ValueError(
                "derived source must have a new source_id"
            )

        if normalized_year == historical_source.academic_year:
            raise ValueError(
                "derived source must target a different academic year"
            )

        if owner_id is None:
            derived_owner = historical_source.owner_id
        else:
            derived_owner = self._required_text(
                owner_id,
                "owner_id",
            )

        if source_name is None:
            derived_name = historical_source.source_name
        else:
            derived_name = self._optional_text(
                source_name,
                "source_name",
            )

        if source_version is None:
            derived_version = historical_source.source_version
        else:
            derived_version = self._optional_text(
                source_version,
                "source_version",
            )

        derived_source = OperationalDataSource(
            source_id=normalized_source_id,
            data_type=historical_source.data_type,
            origin=historical_source.origin,
            owner_id=derived_owner,
            academic_year=normalized_year,
            status=OperationalDataStatus.UPLOADED,
            source_name=derived_name,
            source_version=derived_version,
        )

        input_reference = OperationalInputReference(
            location=OperationalInputLocation.SYSTEM_LIBRARY,
            source_id=historical_source.source_id,
            source_academic_year=(
                historical_source.academic_year
            ),
        )

        return OperationalDataDerivation(
            derived_source=derived_source,
            input_reference=input_reference,
        )

    @staticmethod
    def _validate_source(
        source: OperationalDataSource,
    ) -> None:
        if not isinstance(
            source,
            OperationalDataSource,
        ):
            raise TypeError(
                "source must be OperationalDataSource"
            )

    @staticmethod
    def _validate_status(
        status: OperationalDataStatus,
    ) -> None:
        if not isinstance(
            status,
            OperationalDataStatus,
        ):
            raise TypeError(
                "target_status must be OperationalDataStatus"
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

    @staticmethod
    def _optional_text(
        value: str | None,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be str or None"
            )

        normalized = value.strip()

        return normalized or None
