from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OperationalDataType(str, Enum):
    PPCT = "PPCT"
    TIMETABLE = "TIMETABLE"
    ACADEMIC_WEEK = "ACADEMIC_WEEK"
    WEEKLY_SCHEDULE_TEMPLATE = "WEEKLY_SCHEDULE_TEMPLATE"


class OperationalDataOrigin(str, Enum):
    SYSTEM_GENERATED = "SYSTEM_GENERATED"
    USER_ENTERED = "USER_ENTERED"
    ADMIN_ENTERED = "ADMIN_ENTERED"
    FILE_IMPORTED = "FILE_IMPORTED"


class OperationalDataStatus(str, Enum):
    UPLOADED = "UPLOADED"
    MAPPED = "MAPPED"
    VALIDATED = "VALIDATED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class OperationalDataSource:
    source_id: str
    data_type: OperationalDataType
    origin: OperationalDataOrigin
    owner_id: str
    academic_year: str
    status: OperationalDataStatus
    source_name: str | None = None
    source_version: str | None = None

    def __post_init__(self) -> None:
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

        if not isinstance(
            self.data_type,
            OperationalDataType,
        ):
            raise TypeError(
                "data_type must be OperationalDataType"
            )

        if not isinstance(
            self.origin,
            OperationalDataOrigin,
        ):
            raise TypeError(
                "origin must be OperationalDataOrigin"
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
        if not isinstance(
            value,
            str,
        ):
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

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be str or None"
            )

        normalized = value.strip()

        return normalized or None
