"""Supabase adapter for operational-data source catalog metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from educational_planning_v2.models.operational_data_source import (
    OperationalDataOrigin,
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.repositories.operational_data_source_repository import (
    OperationalDataSourceRepository,
)


class SupabaseOperationalDataSourceRepository(
    OperationalDataSourceRepository
):
    def __init__(
        self,
        client: Any,
        user_id: str,
        table_name: str = "operational_data_sources",
    ) -> None:
        self._client = client
        self._user_id = self._required_text(user_id, "user_id")
        self._table_name = self._required_text(table_name, "table_name")

    @property
    def user_id(self) -> str:
        return self._user_id

    def save(
        self,
        *,
        source: OperationalDataSource,
    ) -> OperationalDataSource:
        if not isinstance(source, OperationalDataSource):
            raise TypeError(
                "source must be OperationalDataSource"
            )

        self._require_owned_source(source)

        row = {
            "user_id": self._user_id,
            "source_id": source.source_id,
            "data_type": source.data_type.value,
            "origin": source.origin.value,
            "owner_id": source.owner_id,
            "academic_year": source.academic_year,
            "status": source.status.value,
            "source_name": source.source_name,
            "source_version": source.source_version,
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        response = (
            self._client
            .table(self._table_name)
            .upsert(
                row,
                on_conflict="user_id,source_id",
            )
            .execute()
        )

        rows = self._response_rows(response)

        if not rows:
            return source

        return self._from_row(rows[0])

    def get(
        self,
        *,
        source_id: str,
    ) -> OperationalDataSource | None:
        normalized = self._required_text(
            source_id,
            "source_id",
        )

        response = (
            self._client
            .table(self._table_name)
            .select(
                "source_id,data_type,origin,owner_id,"
                "academic_year,status,source_name,"
                "source_version"
            )
            .eq("user_id", self._user_id)
            .eq("source_id", normalized)
            .limit(1)
            .execute()
        )

        rows = self._response_rows(response)

        if not rows:
            return None

        source = self._from_row(rows[0])
        self._require_owned_source(source)

        return source

    def list_sources(
        self,
        *,
        owner_id: str | None = None,
        academic_year: str | None = None,
        data_type: OperationalDataType | None = None,
        status: OperationalDataStatus | None = None,
    ) -> tuple[OperationalDataSource, ...]:
        if owner_id is not None:
            normalized_owner = self._required_text(
                owner_id,
                "owner_id",
            )

            if normalized_owner != self._user_id:
                return ()

        if academic_year is not None:
            academic_year = self._required_text(
                academic_year,
                "academic_year",
            )

        if (
            data_type is not None
            and not isinstance(
                data_type,
                OperationalDataType,
            )
        ):
            raise TypeError(
                "data_type must be OperationalDataType or None"
            )

        if (
            status is not None
            and not isinstance(
                status,
                OperationalDataStatus,
            )
        ):
            raise TypeError(
                "status must be OperationalDataStatus or None"
            )

        query = (
            self._client
            .table(self._table_name)
            .select(
                "source_id,data_type,origin,owner_id,"
                "academic_year,status,source_name,"
                "source_version"
            )
            .eq("user_id", self._user_id)
        )

        if academic_year is not None:
            query = query.eq(
                "academic_year",
                academic_year,
            )

        if data_type is not None:
            query = query.eq(
                "data_type",
                data_type.value,
            )

        if status is not None:
            query = query.eq(
                "status",
                status.value,
            )

        response = (
            query
            .order("source_id")
            .execute()
        )

        sources = tuple(
            self._from_row(row)
            for row in self._response_rows(response)
        )

        if not all(
            source.owner_id == self._user_id
            for source in sources
        ):
            raise ValueError(
                "repository returned source owned by another user"
            )

        return sources

    def delete(
        self,
        *,
        source_id: str,
    ) -> None:
        normalized = self._required_text(
            source_id,
            "source_id",
        )

        response = (
            self._client
            .table(self._table_name)
            .delete()
            .eq("user_id", self._user_id)
            .eq("source_id", normalized)
            .execute()
        )

        self._response_rows(response)

    def _require_owned_source(
        self,
        source: OperationalDataSource,
    ) -> None:
        if source.owner_id != self._user_id:
            raise ValueError(
                "operational data source owner "
                "does not match authenticated user"
            )

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> OperationalDataSource:
        if not isinstance(row, dict):
            raise TypeError(
                "Supabase row must be dict"
            )

        return OperationalDataSource(
            source_id=row["source_id"],
            data_type=OperationalDataType(
                row["data_type"]
            ),
            origin=OperationalDataOrigin(
                row["origin"]
            ),
            owner_id=row["owner_id"],
            academic_year=row["academic_year"],
            status=OperationalDataStatus(
                row["status"]
            ),
            source_name=row.get("source_name"),
            source_version=row.get("source_version"),
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

        if not isinstance(rows, list):
            raise TypeError(
                "Supabase response data must be a list"
            )

        return rows

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized
