from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from educational_planning_v2.models.operational_data_source import (
    OperationalDataType,
)


@dataclass(frozen=True)
class OperationalPayloadReference:
    source_id: str
    data_type: OperationalDataType
    payload_version: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_id",
            self._required_text(
                self.source_id,
                "source_id",
            ),
        )

        if not isinstance(
            self.data_type,
            OperationalDataType,
        ):
            raise TypeError(
                "data_type must be OperationalDataType"
            )

        object.__setattr__(
            self,
            "payload_version",
            self._optional_text(
                self.payload_version,
                "payload_version",
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
class OperationalPayloadEnvelope:
    reference: OperationalPayloadReference
    payload: Any

    def __post_init__(self) -> None:
        if not isinstance(
            self.reference,
            OperationalPayloadReference,
        ):
            raise TypeError(
                "reference must be OperationalPayloadReference"
            )

        if self.payload is None:
            raise ValueError(
                "payload must not be None"
            )
