from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)


class SupabaseAdminTeachingAssignmentRepository:
    TABLE_NAME = "teaching_assignments"

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
        assignment: TeachingAssignment,
    ) -> TeachingAssignment:
        if not isinstance(
            assignment,
            TeachingAssignment,
        ):
            raise TypeError(
                "assignment must be TeachingAssignment"
            )

        for field_name, value in (
            ("class_id", assignment.class_id),
            ("subject_ref", assignment.subject_ref),
            ("component_ref", assignment.component_ref),
        ):
            if (
                value is not None
                and (
                    "," in value
                    or ";" in value
                )
            ):
                raise ValueError(
                    f"{field_name} must contain "
                    "exactly one value"
                )

        row = {
            "assignment_id": (
                assignment.assignment_id
            ),
            "owner_id": (
                assignment.owner_id
            ),
            "academic_year": (
                assignment.academic_year
            ),
            "class_id": (
                assignment.class_id
            ),
            "subject_ref": (
                assignment.subject_ref
            ),
            "component_ref": (
                assignment.component_ref
            ),
            "assignment_round_id": (
                assignment.assignment_round_id
            ),
            "role": (
                assignment.role.value
            ),
            "effective_from": (
                assignment.effective_from.isoformat()
            ),
            "effective_to": (
                assignment.effective_to.isoformat()
            ),
            "status": (
                assignment.status.value
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
                on_conflict="assignment_id",
            )
            .execute()
        )

        rows = self._response_rows(
            response
        )

        if not rows:
            return assignment

        return self._from_row(
            rows[0]
        )

    def get(
        self,
        *,
        assignment_id: str,
    ) -> TeachingAssignment | None:
        normalized_id = self._required_text(
            assignment_id,
            "assignment_id",
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "assignment_id",
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

    def list_assignments(
        self,
        *,
        owner_id: str | None = None,
        academic_year: str | None = None,
        role: TeachingAssignmentRole | None = None,
        status: TeachingAssignmentStatus | None = None,
    ) -> tuple[
        TeachingAssignment,
        ...,
    ]:
        query = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
        )

        if owner_id is not None:
            query = query.eq(
                "owner_id",
                self._required_text(
                    owner_id,
                    "owner_id",
                ),
            )

        if academic_year is not None:
            query = query.eq(
                "academic_year",
                self._required_text(
                    academic_year,
                    "academic_year",
                ),
            )

        if role is not None:
            if not isinstance(
                role,
                TeachingAssignmentRole,
            ):
                raise TypeError(
                    "role must be "
                    "TeachingAssignmentRole "
                    "or None"
                )

            query = query.eq(
                "role",
                role.value,
            )

        if status is not None:
            if not isinstance(
                status,
                TeachingAssignmentStatus,
            ):
                raise TypeError(
                    "status must be "
                    "TeachingAssignmentStatus "
                    "or None"
                )

            query = query.eq(
                "status",
                status.value,
            )

        response = (
            query
            .order("academic_year")
            .order("owner_id")
            .order("class_id")
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
        assignment_id: str,
    ) -> None:
        normalized_id = self._required_text(
            assignment_id,
            "assignment_id",
        )

        (
            self._client
            .table(self.TABLE_NAME)
            .delete()
            .eq(
                "assignment_id",
                normalized_id,
            )
            .execute()
        )

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> TeachingAssignment:
        return TeachingAssignment(
            assignment_id=str(
                row["assignment_id"]
            ),
            owner_id=str(
                row["owner_id"]
            ),
            academic_year=str(
                row["academic_year"]
            ),
            class_id=str(
                row["class_id"]
            ),
            subject_ref=(
                None
                if row.get("subject_ref")
                is None
                else str(
                    row["subject_ref"]
                )
            ),
            component_ref=(
                None
                if row.get("component_ref")
                is None
                else str(
                    row["component_ref"]
                )
            ),
            assignment_round_id=(
                None
                if row.get("assignment_round_id")
                is None
                else str(
                    row["assignment_round_id"]
                )
            ),
            role=TeachingAssignmentRole(
                str(
                    row["role"]
                )
            ),
            effective_from=date.fromisoformat(
                str(
                    row["effective_from"]
                )
            ),
            effective_to=date.fromisoformat(
                str(
                    row["effective_to"]
                )
            ),
            status=TeachingAssignmentStatus(
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
