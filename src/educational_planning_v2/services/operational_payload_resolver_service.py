from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.models.operational_data_io import (
    OperationalInputLocation,
)
from educational_planning_v2.models.operational_payload import (
    OperationalPayloadEnvelope,
    OperationalPayloadReference,
)
from educational_planning_v2.repositories.operational_payload_repository import (
    OperationalPayloadRepository,
)
from educational_planning_v2.services.operational_input_selection_service import (
    OperationalInputSelection,
)


@dataclass(frozen=True)
class OperationalPayloadResolution:
    selection: OperationalInputSelection
    envelope: OperationalPayloadEnvelope

    def __post_init__(self) -> None:
        if not isinstance(
            self.selection,
            OperationalInputSelection,
        ):
            raise TypeError(
                "selection must be OperationalInputSelection"
            )

        if not isinstance(
            self.envelope,
            OperationalPayloadEnvelope,
        ):
            raise TypeError(
                "envelope must be OperationalPayloadEnvelope"
            )


class OperationalPayloadResolverService:
    """
    Resolve an operational payload after input-source selection.

    LOCAL_UPLOAD and SYSTEM_GENERATED payloads are supplied by
    the application boundary.

    SYSTEM_LIBRARY payloads are resolved through the abstract
    OperationalPayloadRepository.

    This service performs no physical file or database I/O.
    """

    def __init__(
        self,
        repository: OperationalPayloadRepository,
    ) -> None:
        if not isinstance(
            repository,
            OperationalPayloadRepository,
        ):
            raise TypeError(
                "repository must implement "
                "OperationalPayloadRepository"
            )

        self._repository = repository

    def resolve(
        self,
        *,
        selection: OperationalInputSelection,
        supplied_envelope: OperationalPayloadEnvelope | None = None,
    ) -> OperationalPayloadResolution:
        if not isinstance(
            selection,
            OperationalInputSelection,
        ):
            raise TypeError(
                "selection must be OperationalInputSelection"
            )

        location = selection.reference.location

        if (
            location
            is OperationalInputLocation.SYSTEM_LIBRARY
        ):
            if supplied_envelope is not None:
                raise ValueError(
                    "SYSTEM_LIBRARY payload must be resolved "
                    "from repository"
                )

            return self._resolve_system_library(
                selection=selection,
            )

        if (
            location
            in (
                OperationalInputLocation.LOCAL_UPLOAD,
                OperationalInputLocation.SYSTEM_GENERATED,
            )
        ):
            if supplied_envelope is None:
                raise ValueError(
                    f"{location.value} requires supplied_envelope"
                )

            return OperationalPayloadResolution(
                selection=selection,
                envelope=supplied_envelope,
            )

        raise ValueError(
            "unsupported operational input location"
        )

    def _resolve_system_library(
        self,
        *,
        selection: OperationalInputSelection,
    ) -> OperationalPayloadResolution:
        source = selection.source

        if source is None:
            raise ValueError(
                "SYSTEM_LIBRARY selection requires catalog source"
            )

        reference = OperationalPayloadReference(
            source_id=source.source_id,
            data_type=source.data_type,
            payload_version=source.source_version,
        )

        envelope = self._repository.get(
            reference=reference,
        )

        if envelope is None:
            raise LookupError(
                "operational payload not found for "
                f"source {source.source_id}"
            )

        self._validate_catalog_identity(
            selection=selection,
            envelope=envelope,
        )

        return OperationalPayloadResolution(
            selection=selection,
            envelope=envelope,
        )

    @staticmethod
    def _validate_catalog_identity(
        *,
        selection: OperationalInputSelection,
        envelope: OperationalPayloadEnvelope,
    ) -> None:
        source = selection.source

        if source is None:
            raise ValueError(
                "catalog source is required"
            )

        if (
            envelope.reference.source_id
            != source.source_id
        ):
            raise ValueError(
                "payload source_id does not match catalog source"
            )

        if (
            envelope.reference.data_type
            is not source.data_type
        ):
            raise ValueError(
                "payload data_type does not match catalog source"
            )

        if (
            source.source_version is not None
            and
            envelope.reference.payload_version is not None
            and
            source.source_version
            != envelope.reference.payload_version
        ):
            raise ValueError(
                "payload version does not match catalog version"
            )
