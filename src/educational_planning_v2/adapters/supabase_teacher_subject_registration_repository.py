from __future__ import annotations

from typing import Any

from educational_planning_v2.models.teacher_subject_registration import (
    TeacherSubjectRegistration,
    TeacherSubjectRegistrationStatus,
)
from educational_planning_v2.repositories.teacher_subject_registration_repository import (
    TeacherSubjectRegistrationRepository,
)


class SupabaseTeacherSubjectRegistrationRepository(
    TeacherSubjectRegistrationRepository
):
    TABLE_NAME = "teacher_subject_registrations"

    def __init__(
        self,
        client: Any,
        owner_id: str,
    ) -> None:
        if client is None:
            raise ValueError(
                "client must not be None"
            )

        self._client = client
        self._owner_id = self._required_text(
            owner_id,
            "owner_id",
        )

    def save(
        self,
        *,
        registration: TeacherSubjectRegistration,
    ) -> TeacherSubjectRegistration:
        if not isinstance(
            registration,
            TeacherSubjectRegistration,
        ):
            raise TypeError(
                "registration must be "
                "TeacherSubjectRegistration"
            )

        self._assert_owner(
            registration.owner_id
        )

        row = {
            "registration_id":
                registration.registration_id,
            "owner_id":
                registration.owner_id,
            "academic_year":
                registration.academic_year,
            "subject_id":
                registration.subject_id,
            "component_id":
                registration.component_id,
            "status":
                registration.status.value,
        }

        response = (
            self._client
            .table(self.TABLE_NAME)
            .upsert(
                row,
                on_conflict="registration_id",
            )
            .execute()
        )

        rows = self._response_rows(
            response
        )

        return (
            self._from_row(rows[0])
            if rows
            else registration
        )

    def get(
        self,
        *,
        registration_id: str,
    ) -> TeacherSubjectRegistration | None:
        normalized_id = self._required_text(
            registration_id,
            "registration_id",
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "registration_id",
                normalized_id,
            )
            .eq(
                "owner_id",
                self._owner_id,
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

    def list_registrations(
        self,
        *,
        owner_id: str,
        academic_year: str,
        status: (
            TeacherSubjectRegistrationStatus
            | None
        ) = None,
    ) -> tuple[
        TeacherSubjectRegistration,
        ...
    ]:
        self._assert_owner(
            owner_id
        )

        normalized_year = self._required_text(
            academic_year,
            "academic_year",
        )

        self._validate_status(
            status
        )

        query = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "owner_id",
                self._owner_id,
            )
            .eq(
                "academic_year",
                normalized_year,
            )
        )

        if status is not None:
            query = query.eq(
                "status",
                status.value,
            )

        response = (
            query
            .order("subject_id")
            .order("component_id")
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
        owner_id: str,
        academic_year: str,
        subject_id: str,
        status: (
            TeacherSubjectRegistrationStatus
            | None
        ) = None,
    ) -> tuple[
        TeacherSubjectRegistration,
        ...
    ]:
        self._assert_owner(
            owner_id
        )

        normalized_year = self._required_text(
            academic_year,
            "academic_year",
        )

        normalized_subject = self._required_text(
            subject_id,
            "subject_id",
        )

        self._validate_status(
            status
        )

        query = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "owner_id",
                self._owner_id,
            )
            .eq(
                "academic_year",
                normalized_year,
            )
            .eq(
                "subject_id",
                normalized_subject,
            )
        )

        if status is not None:
            query = query.eq(
                "status",
                status.value,
            )

        response = (
            query
            .order("component_id")
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
        registration_id: str,
    ) -> None:
        normalized_id = self._required_text(
            registration_id,
            "registration_id",
        )

        (
            self._client
            .table(self.TABLE_NAME)
            .delete()
            .eq(
                "registration_id",
                normalized_id,
            )
            .eq(
                "owner_id",
                self._owner_id,
            )
            .execute()
        )

    def _assert_owner(
        self,
        owner_id: str,
    ) -> None:
        normalized = self._required_text(
            owner_id,
            "owner_id",
        )

        if normalized != self._owner_id:
            raise ValueError(
                "owner_id does not match "
                "authenticated owner"
            )

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> TeacherSubjectRegistration:
        component_id = row.get(
            "component_id"
        )

        return TeacherSubjectRegistration(
            registration_id=str(
                row["registration_id"]
            ),
            owner_id=str(
                row["owner_id"]
            ),
            academic_year=str(
                row["academic_year"]
            ),
            subject_id=str(
                row["subject_id"]
            ),
            component_id=(
                None
                if component_id is None
                else str(component_id)
            ),
            status=(
                TeacherSubjectRegistrationStatus(
                    str(row["status"])
                )
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
        status: (
            TeacherSubjectRegistrationStatus
            | None
        ),
    ) -> None:
        if (
            status is not None
            and not isinstance(
                status,
                TeacherSubjectRegistrationStatus,
            )
        ):
            raise TypeError(
                "status must be "
                "TeacherSubjectRegistrationStatus "
                "or None"
            )
