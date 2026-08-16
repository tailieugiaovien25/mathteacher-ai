"""Supabase persistence adapter for operational payloads."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any

from educational_planning_v2.models.operational_data_source import (
    OperationalDataType,
)
from educational_planning_v2.models.operational_payload import (
    OperationalPayloadEnvelope,
    OperationalPayloadReference,
)
from educational_planning_v2.repositories.operational_payload_repository import (
    OperationalPayloadRepository,
)


class SupabaseOperationalPayloadRepository(
    OperationalPayloadRepository
):
    """
    Persist JSON-compatible operational payloads.

    Catalog metadata remains owned by
    OperationalDataSourceRepository.
    """

    def __init__(
        self,
        client: Any,
        user_id: str,
        table_name: str = "operational_payloads",
    ) -> None:
        self._client = client
        self._user_id = self._required_text(
            user_id,
            "user_id",
        )
        self._table_name = self._required_text(
            table_name,
            "table_name",
        )

    @property
    def user_id(self) -> str:
        return self._user_id

    def save(
        self,
        *,
        envelope: OperationalPayloadEnvelope,
    ) -> OperationalPayloadEnvelope:
        if not isinstance(
            envelope,
            OperationalPayloadEnvelope,
        ):
            raise TypeError(
                "envelope must be OperationalPayloadEnvelope"
            )

        self._validate_json_payload(
            envelope.payload
        )

        now = datetime.now(
            timezone.utc
        ).isoformat()

        row = {
            "user_id": self._user_id,
            "source_id": (
                envelope.reference.source_id
            ),
            "data_type": (
                envelope.reference.data_type.value
            ),
            "payload_version": (
                envelope.reference.payload_version
                or ""
            ),
            "payload": envelope.payload,
            "updated_at": now,
        }

        response = (
            self._client
            .table(self._table_name)
            .upsert(
                row,
                on_conflict=(
                    "user_id,source_id,"
                    "data_type,payload_version"
                ),
            )
            .execute()
        )

        rows = self._response_rows(
            response
        )

        if not rows:
            return envelope

        return self._from_row(
            rows[0]
        )

    def get(
        self,
        *,
        reference: OperationalPayloadReference,
    ) -> OperationalPayloadEnvelope | None:
        self._validate_reference(
            reference
        )

        response = (
            self._client
            .table(self._table_name)
            .select(
                "source_id,data_type,"
                "payload_version,payload"
            )
            .eq(
                "user_id",
                self._user_id,
            )
            .eq(
                "source_id",
                reference.source_id,
            )
            .eq(
                "data_type",
                reference.data_type.value,
            )
            .eq(
                "payload_version",
                reference.payload_version or "",
            )
            .limit(1)
            .execute()
        )

        rows = self._response_rows(
            response
        )

        if not rows:
            return None

        return self._from_row(
            rows[0]
        )

    def delete(
        self,
        *,
        reference: OperationalPayloadReference,
    ) -> None:
        self._validate_reference(
            reference
        )

        response = (
            self._client
            .table(self._table_name)
            .delete()
            .eq(
                "user_id",
                self._user_id,
            )
            .eq(
                "source_id",
                reference.source_id,
            )
            .eq(
                "data_type",
                reference.data_type.value,
            )
            .eq(
                "payload_version",
                reference.payload_version or "",
            )
            .execute()
        )

        self._response_rows(
            response
        )

    @staticmethod
    def _validate_reference(
        reference: OperationalPayloadReference,
    ) -> None:
        if not isinstance(
            reference,
            OperationalPayloadReference,
        ):
            raise TypeError(
                "reference must be OperationalPayloadReference"
            )

    @staticmethod
    def _validate_json_payload(
        payload: Any,
    ) -> None:
        try:
            json.dumps(
                payload,
                ensure_ascii=False,
            )
        except (TypeError, ValueError) as error:
            raise TypeError(
                "payload must be JSON-compatible"
            ) from error

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> OperationalPayloadEnvelope:
        version = row.get(
            "payload_version"
        )

        return OperationalPayloadEnvelope(
            reference=OperationalPayloadReference(
                source_id=row["source_id"],
                data_type=OperationalDataType(
                    row["data_type"]
                ),
                payload_version=(
                    version
                    if version
                    else None
                ),
            ),
            payload=row["payload"],
        )

    @staticmethod
    def _response_rows(
        response: Any,
    ) -> list[dict[str, Any]]:
        rows = getattr(
            response,
            "data",
            None,
        )

        if rows is None:
            raise ValueError(
                "Supabase response does not contain data"
            )

        if not isinstance(
            rows,
            list,
        ):
            raise TypeError(
                "Supabase response data must be a list"
            )

        return rows

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
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized
