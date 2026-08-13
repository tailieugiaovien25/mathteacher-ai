from __future__ import annotations

from typing import Any

from curriculum_v2.governance.trusted_admin_data_repository import (
    TrustedAdministrativeDataRepository,
)


class InMemoryTrustedAdministrativeDataRepository(
    TrustedAdministrativeDataRepository
):
    """
    Reference in-memory implementation.

    It owns only temporary process-local state and contains
    no physical-storage dependency.
    """

    def __init__(self) -> None:
        self._records: dict[str, Any] = {}

    def save(
        self,
        *,
        record_id: str,
        record: Any,
    ) -> None:
        record_id = self._normalize_record_id(
            record_id
        )

        self._records[
            record_id
        ] = record

    def get(
        self,
        *,
        record_id: str,
    ) -> Any | None:
        record_id = self._normalize_record_id(
            record_id
        )

        return self._records.get(
            record_id
        )

    def list_records(
        self,
        *,
        record_type: str | None = None,
    ) -> tuple[Any, ...]:
        if record_type is None:
            return tuple(
                self._records.values()
            )

        if not isinstance(
            record_type,
            str,
        ):
            raise TypeError(
                "record_type must be str or None"
            )

        normalized_type = (
            record_type.strip()
        )

        if not normalized_type:
            raise ValueError(
                "record_type must not be empty"
            )

        return tuple(
            record
            for record in self._records.values()
            if (
                type(record).__name__
                == normalized_type
            )
        )

    def delete(
        self,
        *,
        record_id: str,
    ) -> None:
        record_id = self._normalize_record_id(
            record_id
        )

        self._records.pop(
            record_id,
            None,
        )

    @staticmethod
    def _normalize_record_id(
        record_id: str,
    ) -> str:
        if not isinstance(
            record_id,
            str,
        ):
            raise TypeError(
                "record_id must be str"
            )

        normalized = record_id.strip()

        if not normalized:
            raise ValueError(
                "record_id must not be empty"
            )

        return normalized
