from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OperationalInputLocation(str, Enum):
    LOCAL_UPLOAD = "LOCAL_UPLOAD"
    SYSTEM_LIBRARY = "SYSTEM_LIBRARY"
    SYSTEM_GENERATED = "SYSTEM_GENERATED"


class OperationalOutputDestination(str, Enum):
    SYSTEM_STORAGE = "SYSTEM_STORAGE"
    DOWNLOAD = "DOWNLOAD"
    GOOGLE_DRIVE = "GOOGLE_DRIVE"
    VTSMAS = "VTSMAS"


@dataclass(frozen=True)
class OperationalInputReference:
    location: OperationalInputLocation
    source_id: str | None = None
    source_academic_year: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.location,
            OperationalInputLocation,
        ):
            raise TypeError(
                "location must be OperationalInputLocation"
            )

        object.__setattr__(
            self,
            "source_id",
            self._optional_text(
                self.source_id,
                "source_id",
            ),
        )

        object.__setattr__(
            self,
            "source_academic_year",
            self._optional_text(
                self.source_academic_year,
                "source_academic_year",
            ),
        )

        if (
            self.location
            is OperationalInputLocation.SYSTEM_LIBRARY
            and self.source_id is None
        ):
            raise ValueError(
                "SYSTEM_LIBRARY input requires source_id"
            )

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
class OperationalOutputPlan:
    destinations: tuple[OperationalOutputDestination, ...]

    def __post_init__(self) -> None:
        if not isinstance(
            self.destinations,
            tuple,
        ):
            raise TypeError(
                "destinations must be tuple"
            )

        if not self.destinations:
            raise ValueError(
                "at least one output destination is required"
            )

        if not all(
            isinstance(
                destination,
                OperationalOutputDestination,
            )
            for destination in self.destinations
        ):
            raise TypeError(
                "all destinations must be "
                "OperationalOutputDestination"
            )

        normalized = tuple(
            dict.fromkeys(self.destinations)
        )

        object.__setattr__(
            self,
            "destinations",
            normalized,
        )

    def includes(
        self,
        destination: OperationalOutputDestination,
    ) -> bool:
        if not isinstance(
            destination,
            OperationalOutputDestination,
        ):
            raise TypeError(
                "destination must be "
                "OperationalOutputDestination"
            )

        return destination in self.destinations
