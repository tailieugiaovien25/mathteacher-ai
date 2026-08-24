from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
    TeachingAssignmentStatus,
)
from educational_planning_v2.repositories.teaching_assignment_repository import (
    TeachingAssignmentRepository,
)


class SupabaseTeachingAssignmentRepository(
    TeachingAssignmentRepository
):
    def __init__(
        self,
        client: Any,
        user_id: str,
        table_name: str = "teaching_assignments",
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

        if assignment.owner_id != self._user_id:
            raise ValueError(
                "assignment owner does not match "
                "authenticated user"
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
            "assignment_id": assignment.assignment_id,
            "owner_id": assignment.owner_id,
            "academic_year": assignment.academic_year,
            "class_id": assignment.class_id,
            "subject_ref": assignment.subject_ref,
            "component_ref": assignment.component_ref,
            "assignment_round_id": (
                assignment.assignment_round_id
            ),
            "role": assignment.role.value,
            "effective_from": (
                assignment.effective_from.isoformat()
            ),
            "effective_to": (
                assignment.effective_to.isoformat()
            ),
            "status": assignment.status.value,
            "updated_at": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
        }

        response = (
            self._client
            .table(self._table_name)
            .upsert(
                row,
                on_conflict="assignment_id",
            )
            .execute()
        )

        rows = self._response_rows(
            response
        )

        return (
            self._from_row(rows[0])
            if rows
            else assignment
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
            .table(self._table_name)
            .select("*")
            .eq(
                "assignment_id",
                normalized_id,
            )
            .eq(
                "owner_id",
                self._user_id,
            )
            .limit(1)
            .execute()
        )

        rows = self._response_rows(
            response
        )

        return (
            self._from_row(rows[0])
            if rows
            else None
        )

    def list_assignments(
        self,
        *,
        owner_id: str,
        academic_year: str,
        role: TeachingAssignmentRole | None = None,
        status: TeachingAssignmentStatus | None = None,
    ) -> tuple[TeachingAssignment, ...]:
        normalized_owner = self._required_text(
            owner_id,
            "owner_id",
        )

        normalized_year = self._required_text(
            academic_year,
            "academic_year",
        )

        if normalized_owner != self._user_id:
            raise ValueError(
                "owner_id does not match "
                "authenticated user"
            )

        if (
            role is not None
            and not isinstance(
                role,
                TeachingAssignmentRole,
            )
        ):
            raise TypeError(
                "role must be "
                "TeachingAssignmentRole or None"
            )

        if (
            status is not None
            and not isinstance(
                status,
                TeachingAssignmentStatus,
            )
        ):
            raise TypeError(
                "status must be "
                "TeachingAssignmentStatus or None"
            )

        query = (
            self._client
            .table(self._table_name)
            .select("*")
            .eq(
                "owner_id",
                normalized_owner,
            )
            .eq(
                "academic_year",
                normalized_year,
            )
        )

        if role is not None:
            query = query.eq(
                "role",
                role.value,
            )

        if status is not None:
            query = query.eq(
                "status",
                status.value,
            )

        response = query.execute()

        rows = self._response_rows(
            response
        )

        return tuple(
            self._from_row(row)
            for row in rows
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
            .table(self._table_name)
            .delete()
            .eq(
                "assignment_id",
                normalized_id,
            )
            .eq(
                "owner_id",
                self._user_id,
            )
            .execute()
        )

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> TeachingAssignment:
        return TeachingAssignment(
            assignment_id=row["assignment_id"],
            owner_id=row["owner_id"],
            academic_year=row["academic_year"],
            class_id=row["class_id"],
            subject_ref=row.get(
                "subject_ref"
            ),
            component_ref=row.get(
                "component_ref"
            ),
            assignment_round_id=row.get(
                "assignment_round_id"
            ),
            role=TeachingAssignmentRole(
                row["role"]
            ),
            effective_from=date.fromisoformat(
                row["effective_from"]
            ),
            effective_to=date.fromisoformat(
                row["effective_to"]
            ),
            status=TeachingAssignmentStatus(
                row["status"]
            ),
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
                "Supabase response data "
                "must be a list"
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
