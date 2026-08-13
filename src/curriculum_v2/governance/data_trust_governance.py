from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class DataTrustLevel(str, Enum):
    """
    Trust classification is independent from physical storage
    and from concrete educational values.
    """

    OFFICIAL_AUTHORITY = "OFFICIAL_AUTHORITY"
    ADMIN_VERIFIED = "ADMIN_VERIFIED"
    USER_INPUT = "USER_INPUT"
    SYSTEM_DERIVED = "SYSTEM_DERIVED"


class VerificationStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class AdministrativeVerification:
    entered_by: str
    verified_by: str
    verified_at: datetime
    source_reference: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("entered_by", "verified_by"):
            value = getattr(self, field_name)

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

        if not isinstance(
            self.verified_at,
            datetime,
        ):
            raise TypeError(
                "verified_at must be datetime"
            )

        if self.source_reference is not None:
            if not isinstance(
                self.source_reference,
                str,
            ):
                raise TypeError(
                    "source_reference must be str or None"
                )

            normalized_source = (
                self.source_reference.strip()
            )

            if not normalized_source:
                raise ValueError(
                    "source_reference must not be empty"
                )

            object.__setattr__(
                self,
                "source_reference",
                normalized_source,
            )


@dataclass(frozen=True)
class DataGovernanceRecord:
    record_id: str
    trust_level: DataTrustLevel
    verification_status: VerificationStatus
    administrative_verification: (
        AdministrativeVerification | None
    ) = None
    metadata: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, str):
            raise TypeError(
                "record_id must be str"
            )

        normalized_id = self.record_id.strip()

        if not normalized_id:
            raise ValueError(
                "record_id must not be empty"
            )

        object.__setattr__(
            self,
            "record_id",
            normalized_id,
        )

        if not isinstance(
            self.trust_level,
            DataTrustLevel,
        ):
            raise TypeError(
                "trust_level must be DataTrustLevel"
            )

        if not isinstance(
            self.verification_status,
            VerificationStatus,
        ):
            raise TypeError(
                "verification_status must be VerificationStatus"
            )

        admin_verification = (
            self.administrative_verification
        )

        if (
            self.trust_level
            is DataTrustLevel.ADMIN_VERIFIED
        ):
            if not isinstance(
                admin_verification,
                AdministrativeVerification,
            ):
                raise ValueError(
                    "ADMIN_VERIFIED data requires "
                    "AdministrativeVerification"
                )

            if (
                self.verification_status
                is not VerificationStatus.VERIFIED
            ):
                raise ValueError(
                    "ADMIN_VERIFIED data must have "
                    "VERIFIED status"
                )

        elif admin_verification is not None:
            raise ValueError(
                "AdministrativeVerification is only "
                "valid for ADMIN_VERIFIED data"
            )

        if (
            self.trust_level
            is DataTrustLevel.SYSTEM_DERIVED
            and self.verification_status
            is VerificationStatus.VERIFIED
        ):
            raise ValueError(
                "SYSTEM_DERIVED data cannot promote "
                "itself directly to VERIFIED"
            )

        metadata = self.metadata

        if metadata is None:
            metadata = {}

        if not isinstance(metadata, Mapping):
            raise TypeError(
                "metadata must be a mapping"
            )

        normalized_metadata: dict[str, str] = {}

        for key, value in metadata.items():
            if not isinstance(key, str):
                raise TypeError(
                    "metadata keys must be str"
                )

            if not isinstance(value, str):
                raise TypeError(
                    "metadata values must be str"
                )

            normalized_key = key.strip()
            normalized_value = value.strip()

            if not normalized_key:
                raise ValueError(
                    "metadata key must not be empty"
                )

            normalized_metadata[
                normalized_key
            ] = normalized_value

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                normalized_metadata
            ),
        )


def is_trusted_for_production(
    record: DataGovernanceRecord,
) -> bool:
    """
    A trust decision is policy-owned.

    OFFICIAL_AUTHORITY is trusted only when VERIFIED.
    ADMIN_VERIFIED is trusted only when VERIFIED.
    USER_INPUT and SYSTEM_DERIVED are not automatically
    authoritative production data.
    """

    if not isinstance(
        record,
        DataGovernanceRecord,
    ):
        raise TypeError(
            "record must be DataGovernanceRecord"
        )

    return (
        record.verification_status
        is VerificationStatus.VERIFIED
        and record.trust_level
        in {
            DataTrustLevel.OFFICIAL_AUTHORITY,
            DataTrustLevel.ADMIN_VERIFIED,
        }
    )
