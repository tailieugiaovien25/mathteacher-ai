from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeAllocationProvenance:
    """
    Provenance for an authoritative time-allocation record.

    This contract stores logical authority/provenance information only.
    It MUST NOT contain physical file paths, database locations,
    URLs, or storage-specific state.
    """

    legal_authority: str
    regulation_id: str
    source_document_id: str
    source_location: str | None = None
    source_version: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "legal_authority",
            "regulation_id",
            "source_document_id",
        ):
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

        for field_name in (
            "source_location",
            "source_version",
        ):
            value = getattr(self, field_name)

            if value is None:
                continue

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be str or None"
                )

            normalized = value.strip()

            object.__setattr__(
                self,
                field_name,
                normalized or None,
            )


@dataclass(frozen=True)
class CanonicalTimeAllocation:
    """
    Canonical authoritative time-allocation record.

    The contract describes an allocation declared by an educational
    authority dataset. It does not decide or infer how many periods
    a subject or grade should have.

    Concrete educational values belong to versioned authority data,
    never to this contract.
    """

    allocation_id: str
    curriculum_ref: str
    subject_ref: str
    grade: int
    total_periods: int
    provenance: TimeAllocationProvenance
    status: str = "CANDIDATE"
    schema_version: int = 1

    _ALLOWED_STATUSES = (
        "CANDIDATE",
        "VERIFIED",
        "SUPERSEDED",
        "RETIRED",
    )

    def __post_init__(self) -> None:
        for field_name in (
            "allocation_id",
            "curriculum_ref",
            "subject_ref",
        ):
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

        if not isinstance(
            self.provenance,
            TimeAllocationProvenance,
        ):
            raise TypeError(
                "provenance must be TimeAllocationProvenance"
            )

        if not isinstance(self.status, str):
            raise TypeError(
                "status must be str"
            )

        status = self.status.strip().upper()

        if status not in self._ALLOWED_STATUSES:
            raise ValueError(
                "invalid time allocation status"
            )

        object.__setattr__(
            self,
            "status",
            status,
        )

        if (
            not isinstance(self.schema_version, int)
            or isinstance(self.schema_version, bool)
        ):
            raise TypeError(
                "schema_version must be int"
            )

        if self.schema_version <= 0:
            raise ValueError(
                "schema_version must be positive"
            )
