from __future__ import annotations

from typing import Any

from educational_planning_v2.models.teacher_subject_assignment import (
    TeacherSubjectAssignment,
    TeacherSubjectAssignmentStatus,
)
from educational_planning_v2.repositories.teacher_subject_assignment_repository import (
    TeacherSubjectAssignmentRepository,
)


class SupabaseTeacherSubjectAssignmentRepository(
    TeacherSubjectAssignmentRepository
):
    TABLE_NAME = "teacher_subject_assignments"

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
        assignment: TeacherSubjectAssignment,
    ) -> TeacherSubjectAssignment:
        if not isinstance(
            assignment,
            TeacherSubjectAssignment,
        ):
            raise TypeError(
                "assignment must be "
                "TeacherSubjectAssignment"
            )

        payload = {
            "assignment_id": (
                assignment.assignment_id
            ),
            "teacher_id": (
                assignment.teacher_id
            ),
            "academic_year": (
                assignment.academic_year
            ),
            "subject_id": (
                assignment.subject_id
            ),
            "status": (
                assignment.status.value
            ),
        }

        response = (
            self._client
            .table(self.TABLE_NAME)
            .upsert(
                payload,
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
    ) -> TeacherSubjectAssignment | None:
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
        teacher_id: str | None = None,
        academic_year: str | None = None,
        status: TeacherSubjectAssignmentStatus | None = None,
    ) -> tuple[
        TeacherSubjectAssignment,
        ...,
    ]:
        query = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
        )

        if teacher_id is not None:
            query = query.eq(
                "teacher_id",
                self._required_text(
                    teacher_id,
                    "teacher_id",
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

        if status is not None:
            if not isinstance(
                status,
                TeacherSubjectAssignmentStatus,
            ):
                raise TypeError(
                    "status must be "
                    "TeacherSubjectAssignmentStatus "
                    "or None"
                )

            query = query.eq(
                "status",
                status.value,
            )

        response = (
            query
            .order("academic_year")
            .order("subject_id")
            .execute()
        )

        return tuple(
            self._from_row(row)
            for row in self._response_rows(
                response
            )
        )

    def find_subject_scope(
        self,
        *,
        teacher_id: str,
        academic_year: str,
        subject_id: str,
        status: TeacherSubjectAssignmentStatus | None = None,
    ) -> tuple[
        TeacherSubjectAssignment,
        ...,
    ]:
        query = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "teacher_id",
                self._required_text(
                    teacher_id,
                    "teacher_id",
                ),
            )
            .eq(
                "academic_year",
                self._required_text(
                    academic_year,
                    "academic_year",
                ),
            )
            .eq(
                "subject_id",
                self._required_text(
                    subject_id,
                    "subject_id",
                ),
            )
        )

        if status is not None:
            if not isinstance(
                status,
                TeacherSubjectAssignmentStatus,
            ):
                raise TypeError(
                    "status must be "
                    "TeacherSubjectAssignmentStatus "
                    "or None"
                )

            query = query.eq(
                "status",
                status.value,
            )

        response = query.execute()

        return tuple(
            self._from_row(row)
            for row in self._response_rows(
                response
            )
        )

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> TeacherSubjectAssignment:
        return TeacherSubjectAssignment(
            assignment_id=str(
                row["assignment_id"]
            ),
            teacher_id=str(
                row["teacher_id"]
            ),
            academic_year=str(
                row["academic_year"]
            ),
            subject_id=str(
                row["subject_id"]
            ),
            status=(
                TeacherSubjectAssignmentStatus(
                    str(
                        row["status"]
                    )
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
                "Supabase response data must be a list"
            )

        if not all(
            isinstance(
                row,
                dict,
            )
            for row in data
        ):
            raise TypeError(
                "Supabase response rows must be dict"
            )

        return data
