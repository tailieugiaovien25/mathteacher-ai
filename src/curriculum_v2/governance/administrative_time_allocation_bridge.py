from __future__ import annotations

from dataclasses import dataclass

from curriculum_v2.governance.administrative_data_workflow import (
    AdministrativeDataState,
    AdministrativeDataSubmission,
)
from curriculum_v2.governance.data_trust_governance import (
    AdministrativeVerification,
    DataGovernanceRecord,
    DataTrustLevel,
    VerificationStatus,
    is_trusted_for_production,
)
from curriculum_v2.models.canonical_time_allocation import (
    CanonicalTimeAllocation,
    TimeAllocationProvenance,
)


@dataclass(frozen=True)
class AdministrativeTimeAllocationPayload:
    """
    Secondary administrative data waiting to be promoted
    into canonical time-allocation data after governance approval.
    """

    allocation_id: str
    curriculum_ref: str
    subject_ref: str
    grade: int
    total_periods: int

    legal_authority: str
    regulation_id: str
    source_document_id: str

    source_location: str | None = None
    source_version: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "allocation_id",
            "curriculum_ref",
            "subject_ref",
            "legal_authority",
            "regulation_id",
            "source_document_id",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be str"
                )

            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"{field_name} must not be empty"
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )

        if (
            not isinstance(self.grade, int)
            or isinstance(self.grade, bool)
        ):
            raise TypeError(
                "grade must be int"
            )

        if self.grade <= 0:
            raise ValueError(
                "grade must be positive"
            )

        if (
            not isinstance(self.total_periods, int)
            or isinstance(self.total_periods, bool)
        ):
            raise TypeError(
                "total_periods must be int"
            )

        if self.total_periods <= 0:
            raise ValueError(
                "total_periods must be positive"
            )


@dataclass(frozen=True)
class PublishedAdministrativeTimeAllocation:
    canonical_allocation: CanonicalTimeAllocation
    governance_record: DataGovernanceRecord
    submission: AdministrativeDataSubmission


class AdministrativeTimeAllocationPublicationBridge:
    """
    Promotes only PUBLISHED administrative submissions into
    trusted canonical time-allocation data.
    """

    @staticmethod
    def publish(
        *,
        payload: AdministrativeTimeAllocationPayload,
        submission: AdministrativeDataSubmission,
        verification: AdministrativeVerification,
    ) -> PublishedAdministrativeTimeAllocation:
        if not isinstance(
            payload,
            AdministrativeTimeAllocationPayload,
        ):
            raise TypeError(
                "payload must be AdministrativeTimeAllocationPayload"
            )

        if not isinstance(
            submission,
            AdministrativeDataSubmission,
        ):
            raise TypeError(
                "submission must be AdministrativeDataSubmission"
            )

        if not isinstance(
            verification,
            AdministrativeVerification,
        ):
            raise TypeError(
                "verification must be AdministrativeVerification"
            )

        if (
            submission.state
            is not AdministrativeDataState.PUBLISHED
        ):
            raise ValueError(
                "only PUBLISHED administrative submissions "
                "can produce canonical time allocation"
            )

        governance_record = DataGovernanceRecord(
            record_id=(
                f"GOV-{submission.submission_id}"
            ),
            trust_level=DataTrustLevel.ADMIN_VERIFIED,
            verification_status=VerificationStatus.VERIFIED,
            administrative_verification=verification,
            metadata={
                "submission_id":
                    submission.submission_id,
                "submission_version":
                    str(submission.version),
                "audit_event_count":
                    str(len(submission.audit_trail)),
            },
        )

        if not is_trusted_for_production(
            governance_record
        ):
            raise ValueError(
                "governance record is not trusted for production"
            )

        canonical = CanonicalTimeAllocation(
            allocation_id=payload.allocation_id,
            curriculum_ref=payload.curriculum_ref,
            subject_ref=payload.subject_ref,
            grade=payload.grade,
            total_periods=payload.total_periods,
            provenance=TimeAllocationProvenance(
                legal_authority=payload.legal_authority,
                regulation_id=payload.regulation_id,
                source_document_id=payload.source_document_id,
                source_location=payload.source_location,
                source_version=payload.source_version,
            ),
            status="VERIFIED",
            schema_version=1,
        )

        return PublishedAdministrativeTimeAllocation(
            canonical_allocation=canonical,
            governance_record=governance_record,
            submission=submission,
        )
