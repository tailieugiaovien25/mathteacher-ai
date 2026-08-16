from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.adapters.ppct_workbook_upload_adapter import (
    PPCTWorkbookUploadAdapter,
)
from educational_planning_v2.models.operational_data_lifecycle import (
    OperationalDataLifecyclePolicy,
)
from educational_planning_v2.models.operational_data_source import (
    OperationalDataOrigin,
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.models.operational_payload import (
    OperationalPayloadEnvelope,
)
from educational_planning_v2.repositories.operational_data_source_repository import (
    OperationalDataSourceRepository,
)
from educational_planning_v2.repositories.operational_payload_repository import (
    OperationalPayloadRepository,
)


@dataclass(frozen=True)
class PPCTImportRequest:
    owner_id: str
    academic_year: str
    source_id: str
    source_name: str | None = None
    source_version: str | None = None

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

        object.__setattr__(
            self,
            "source_id",
            self._required_text(
                self.source_id,
                "source_id",
            ),
        )

        object.__setattr__(
            self,
            "source_name",
            self._optional_text(
                self.source_name,
                "source_name",
            ),
        )

        object.__setattr__(
            self,
            "source_version",
            self._optional_text(
                self.source_version,
                "source_version",
            ),
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


@dataclass(frozen=True)
class PPCTImportResult:
    source: OperationalDataSource
    envelope: OperationalPayloadEnvelope

    def __post_init__(self) -> None:
        if not isinstance(
            self.source,
            OperationalDataSource,
        ):
            raise TypeError(
                "source must be OperationalDataSource"
            )

        if not isinstance(
            self.envelope,
            OperationalPayloadEnvelope,
        ):
            raise TypeError(
                "envelope must be OperationalPayloadEnvelope"
            )

        if (
            self.source.status
            is not OperationalDataStatus.ACTIVE
        ):
            raise ValueError(
                "import result source must be ACTIVE"
            )


class PPCTImportService:
    """
    Coordinate PPCT workbook import.

    Physical workbook parsing belongs to the upload adapter.
    Metadata persistence belongs to the source repository.
    Payload persistence belongs to the payload repository.
    Lifecycle transitions belong to OperationalDataLifecyclePolicy.
    """

    def __init__(
        self,
        *,
        source_repository: OperationalDataSourceRepository,
        payload_repository: OperationalPayloadRepository,
        upload_adapter: PPCTWorkbookUploadAdapter | None = None,
        lifecycle_policy: OperationalDataLifecyclePolicy | None = None,
    ) -> None:
        if not isinstance(
            source_repository,
            OperationalDataSourceRepository,
        ):
            raise TypeError(
                "source_repository must implement "
                "OperationalDataSourceRepository"
            )

        if not isinstance(
            payload_repository,
            OperationalPayloadRepository,
        ):
            raise TypeError(
                "payload_repository must implement "
                "OperationalPayloadRepository"
            )

        if upload_adapter is None:
            upload_adapter = PPCTWorkbookUploadAdapter()

        if not isinstance(
            upload_adapter,
            PPCTWorkbookUploadAdapter,
        ):
            raise TypeError(
                "upload_adapter must be "
                "PPCTWorkbookUploadAdapter"
            )

        if lifecycle_policy is None:
            lifecycle_policy = OperationalDataLifecyclePolicy()

        if not isinstance(
            lifecycle_policy,
            OperationalDataLifecyclePolicy,
        ):
            raise TypeError(
                "lifecycle_policy must be "
                "OperationalDataLifecyclePolicy"
            )

        self._source_repository = source_repository
        self._payload_repository = payload_repository
        self._upload_adapter = upload_adapter
        self._lifecycle_policy = lifecycle_policy

    def import_workbook(
        self,
        *,
        request: PPCTImportRequest,
        workbook_bytes: bytes,
    ) -> PPCTImportResult:
        if not isinstance(
            request,
            PPCTImportRequest,
        ):
            raise TypeError(
                "request must be PPCTImportRequest"
            )

        envelope = self._upload_adapter.build_envelope(
            workbook_bytes=workbook_bytes,
            source_id=request.source_id,
            payload_version=request.source_version,
        )

        if (
            envelope.reference.data_type
            is not OperationalDataType.PPCT
        ):
            raise ValueError(
                "PPCT import requires PPCT payload"
            )

        source = OperationalDataSource(
            source_id=request.source_id,
            data_type=OperationalDataType.PPCT,
            origin=OperationalDataOrigin.FILE_IMPORTED,
            owner_id=request.owner_id,
            academic_year=request.academic_year,
            status=OperationalDataStatus.UPLOADED,
            source_name=request.source_name,
            source_version=request.source_version,
        )

        source = self._source_repository.save(
            source=source,
        )

        self._payload_repository.save(
            envelope=envelope,
        )

        source = self._transition_and_save(
            source=source,
            target_status=OperationalDataStatus.MAPPED,
        )

        source = self._transition_and_save(
            source=source,
            target_status=OperationalDataStatus.VALIDATED,
        )

        source = self._transition_and_save(
            source=source,
            target_status=OperationalDataStatus.ACTIVE,
        )

        return PPCTImportResult(
            source=source,
            envelope=envelope,
        )

    def _transition_and_save(
        self,
        *,
        source: OperationalDataSource,
        target_status: OperationalDataStatus,
    ) -> OperationalDataSource:
        transitioned = self._lifecycle_policy.transition(
            source=source,
            target_status=target_status,
        )

        return self._source_repository.save(
            source=transitioned,
        )
