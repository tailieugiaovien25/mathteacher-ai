from __future__ import annotations

from typing import Any

from educational_planning_v2.models.subject_catalog import (
    CatalogStatus,
    Subject,
    SubjectComponent,
    SubjectComponentPolicy,
)
from educational_planning_v2.repositories.subject_catalog_repository import (
    SubjectCatalogRepository,
)


class SupabaseSubjectCatalogRepository(
    SubjectCatalogRepository
):
    SUBJECT_TABLE = "subjects"
    COMPONENT_TABLE = "subject_components"

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

    def save_subject(
        self,
        *,
        subject: Subject,
    ) -> Subject:
        if not isinstance(
            subject,
            Subject,
        ):
            raise TypeError(
                "subject must be Subject"
            )

        row = {
            "subject_id": subject.subject_id,
            "code": subject.code,
            "name": subject.name,
            "component_policy": (
                subject.component_policy.value
            ),
            "status": subject.status.value,
            "display_order": subject.display_order,
        }

        response = (
            self._client
            .table(self.SUBJECT_TABLE)
            .upsert(
                row,
                on_conflict="subject_id",
            )
            .execute()
        )

        rows = self._response_rows(
            response
        )

        return (
            self._subject_from_row(rows[0])
            if rows
            else subject
        )

    def save_component(
        self,
        *,
        component: SubjectComponent,
    ) -> SubjectComponent:
        if not isinstance(
            component,
            SubjectComponent,
        ):
            raise TypeError(
                "component must be SubjectComponent"
            )

        row = {
            "component_id": component.component_id,
            "subject_id": component.subject_id,
            "code": component.code,
            "name": component.name,
            "status": component.status.value,
            "display_order": component.display_order,
            "description": component.description,
        }

        response = (
            self._client
            .table(self.COMPONENT_TABLE)
            .upsert(
                row,
                on_conflict="component_id",
            )
            .execute()
        )

        rows = self._response_rows(
            response
        )

        return (
            self._component_from_row(rows[0])
            if rows
            else component
        )

    def get_subject(
        self,
        *,
        subject_id: str,
    ) -> Subject | None:
        normalized_id = self._required_text(
            subject_id,
            "subject_id",
        )

        response = (
            self._client
            .table(self.SUBJECT_TABLE)
            .select("*")
            .eq(
                "subject_id",
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

        return self._subject_from_row(
            rows[0]
        )

    def get_component(
        self,
        *,
        component_id: str,
    ) -> SubjectComponent | None:
        normalized_id = self._required_text(
            component_id,
            "component_id",
        )

        response = (
            self._client
            .table(self.COMPONENT_TABLE)
            .select("*")
            .eq(
                "component_id",
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

        return self._component_from_row(
            rows[0]
        )

    def list_subjects(
        self,
        *,
        status: CatalogStatus | None = None,
    ) -> tuple[Subject, ...]:
        self._validate_status(
            status
        )

        query = (
            self._client
            .table(self.SUBJECT_TABLE)
            .select("*")
        )

        if status is not None:
            query = query.eq(
                "status",
                status.value,
            )

        response = (
            query
            .order("display_order")
            .order("name")
            .execute()
        )

        return tuple(
            self._subject_from_row(row)
            for row in self._response_rows(
                response
            )
        )

    def list_components(
        self,
        *,
        subject_id: str | None = None,
        status: CatalogStatus | None = None,
    ) -> tuple[SubjectComponent, ...]:
        normalized_subject_id = None

        if subject_id is not None:
            normalized_subject_id = (
                self._required_text(
                    subject_id,
                    "subject_id",
                )
            )

        self._validate_status(
            status
        )

        query = (
            self._client
            .table(self.COMPONENT_TABLE)
            .select("*")
        )

        if normalized_subject_id is not None:
            query = query.eq(
                "subject_id",
                normalized_subject_id,
            )

        if status is not None:
            query = query.eq(
                "status",
                status.value,
            )

        response = (
            query
            .order("display_order")
            .order("name")
            .execute()
        )

        return tuple(
            self._component_from_row(row)
            for row in self._response_rows(
                response
            )
        )

    @staticmethod
    def _subject_from_row(
        row: dict[str, Any],
    ) -> Subject:
        return Subject(
            subject_id=str(
                row["subject_id"]
            ),
            code=str(
                row["code"]
            ),
            name=str(
                row["name"]
            ),
            component_policy=(
                SubjectComponentPolicy(
                    str(
                        row[
                            "component_policy"
                        ]
                    )
                )
            ),
            status=CatalogStatus(
                str(
                    row["status"]
                )
            ),
            display_order=int(
                row.get(
                    "display_order",
                    0,
                )
            ),
        )

    @staticmethod
    def _component_from_row(
        row: dict[str, Any],
    ) -> SubjectComponent:
        description = row.get(
            "description"
        )

        return SubjectComponent(
            component_id=str(
                row["component_id"]
            ),
            subject_id=str(
                row["subject_id"]
            ),
            code=str(
                row["code"]
            ),
            name=str(
                row["name"]
            ),
            status=CatalogStatus(
                str(
                    row["status"]
                )
            ),
            display_order=int(
                row.get(
                    "display_order",
                    0,
                )
            ),
            description=(
                None
                if description is None
                else str(description)
            ),
        )

    @staticmethod
    def _response_rows(
        response: Any,
    ) -> list[dict[str, Any]]:
        data = getattr(
            response,
            "data",
            None,
        )

        if not isinstance(
            data,
            list,
        ):
            return []

        return [
            row
            for row in data
            if isinstance(
                row,
                dict,
            )
        ]

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
    def _validate_status(
        status: CatalogStatus | None,
    ) -> None:
        if (
            status is not None
            and not isinstance(
                status,
                CatalogStatus,
            )
        ):
            raise TypeError(
                "status must be "
                "CatalogStatus or None"
            )
