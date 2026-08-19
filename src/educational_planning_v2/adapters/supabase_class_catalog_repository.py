from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from educational_planning_v2.models.class_catalog import (
    ClassCatalog,
    ClassCatalogStatus,
)
from educational_planning_v2.repositories.class_catalog_repository import (
    ClassCatalogRepository,
)


class SupabaseClassCatalogRepository(
    ClassCatalogRepository,
):
    TABLE_NAME = "class_catalogs"

    def __init__(
        self,
        *,
        client: Any,
    ) -> None:
        if client is None:
            raise ValueError(
                "client must not be None"
            )

        self._client = client

    def save(
        self,
        *,
        class_item: ClassCatalog,
    ) -> ClassCatalog:
        if not isinstance(
            class_item,
            ClassCatalog,
        ):
            raise TypeError(
                "class_item must be ClassCatalog"
            )

        row = {
            "class_id": class_item.class_id,
            "academic_year": (
                class_item.academic_year
            ),
            "grade_level": (
                class_item.grade_level
            ),
            "class_code": (
                class_item.class_code
            ),
            "class_name": (
                class_item.class_name
            ),
            "status": (
                class_item.status.value
            ),
            "updated_at": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
        }

        response = (
            self._client
            .table(self.TABLE_NAME)
            .upsert(
                row,
                on_conflict="class_id",
            )
            .execute()
        )

        rows = self._response_rows(
            response
        )

        if rows:
            return self._from_row(
                rows[0]
            )

        # Supabase/PostgREST may return no representation.
        # Never treat that as proof that the write succeeded.
        verified = self.get(
            class_id=class_item.class_id,
        )

        if verified is None:
            raise RuntimeError(
                "Supabase did not persist class "
                f"{class_item.class_id!r}. "
                "Check authenticated ADMIN session, "
                "RLS policies and table privileges."
            )

        if (
            verified.academic_year
            != class_item.academic_year
            or verified.grade_level
            != class_item.grade_level
            or verified.class_code
            != class_item.class_code
            or verified.class_name
            != class_item.class_name
            or verified.status
            != class_item.status
        ):
            raise RuntimeError(
                "Supabase class write verification failed "
                f"for {class_item.class_id!r}."
            )

        return verified

    def get(
        self,
        *,
        class_id: str,
    ) -> ClassCatalog | None:
        normalized_id = self._required_text(
            class_id,
            "class_id",
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "class_id",
                normalized_id,
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

    def list_classes(
        self,
        *,
        academic_year: str,
        grade_level: str | None = None,
        status: ClassCatalogStatus | None = None,
    ) -> tuple[
        ClassCatalog,
        ...,
    ]:
        normalized_year = self._required_text(
            academic_year,
            "academic_year",
        )

        query = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "academic_year",
                normalized_year,
            )
        )

        if grade_level is not None:
            normalized_grade = (
                self._required_text(
                    grade_level,
                    "grade_level",
                )
            )

            query = query.eq(
                "grade_level",
                normalized_grade,
            )

        if status is not None:
            if not isinstance(
                status,
                ClassCatalogStatus,
            ):
                raise TypeError(
                    "status must be "
                    "ClassCatalogStatus or None"
                )

            query = query.eq(
                "status",
                status.value,
            )

        response = (
            query
            .order(
                "grade_level"
            )
            .order(
                "class_code"
            )
            .execute()
        )

        return tuple(
            self._from_row(row)
            for row in self._response_rows(
                response
            )
        )

    def delete(
        self,
        *,
        class_id: str,
    ) -> None:
        normalized_id = self._required_text(
            class_id,
            "class_id",
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .delete()
            .eq(
                "class_id",
                normalized_id,
            )
            .execute()
        )

        rows = self._response_rows(
            response
        )

        # A returned row is useful evidence, but the final
        # source of truth is a read-after-delete verification.
        remaining = self.get(
            class_id=normalized_id,
        )

        if remaining is not None:
            raise RuntimeError(
                "Supabase did not delete class "
                f"{normalized_id!r}. "
                "The row still exists after DELETE. "
                "Check authenticated ADMIN session, "
                "RLS policies and table privileges."
            )

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> ClassCatalog:
        return ClassCatalog(
            class_id=str(
                row["class_id"]
            ),
            academic_year=str(
                row["academic_year"]
            ),
            grade_level=str(
                row["grade_level"]
            ),
            class_code=str(
                row["class_code"]
            ),
            class_name=str(
                row["class_name"]
            ),
            status=ClassCatalogStatus(
                str(
                    row["status"]
                )
            ),
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
    def _response_rows(
        response: Any,
    ) -> list[dict[str, Any]]:
        data = getattr(
            response,
            "data",
            None,
        )

        if data is None:
            return []

        if not isinstance(
            data,
            list,
        ):
            raise TypeError(
                "Supabase response data "
                "must be a list"
            )

        if not all(
            isinstance(
                row,
                dict,
            )
            for row in data
        ):
            raise TypeError(
                "Supabase response rows "
                "must be dict"
            )

        return data
